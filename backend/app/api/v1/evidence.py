"""Evidence artifact endpoints – upload, list, verify integrity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, select

from app.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models.evidence import ArtifactType, EvidenceArtifact, RetentionTag
from app.schemas.common import PaginatedResponse
from app.schemas.evidence import EvidenceResponse
from app.services.audit_events import emit_evidence_stored
from app.services.evidence import create_evidence_artifact
from app.services.storage import storage_client

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", response_model=PaginatedResponse[EvidenceResponse])
async def list_evidence(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    artifact_type: ArtifactType | None = None,
    use_case_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    query = select(EvidenceArtifact)
    count_query = select(func.count()).select_from(EvidenceArtifact)

    if artifact_type:
        query = query.where(EvidenceArtifact.artifact_type == artifact_type)
        count_query = count_query.where(EvidenceArtifact.artifact_type == artifact_type)
    if use_case_id:
        query = query.where(EvidenceArtifact.use_case_id == use_case_id)
        count_query = count_query.where(EvidenceArtifact.use_case_id == use_case_id)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.offset(offset).limit(page_size).order_by(EvidenceArtifact.created_at.desc())
    )
    artifacts = result.scalars().all()

    return PaginatedResponse(
        items=[EvidenceResponse.model_validate(a) for a in artifacts],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=EvidenceResponse, status_code=201)
async def upload_evidence(
    name: str = Form(...),
    artifact_type: ArtifactType = Form(...),
    content_type: str = Form("application/json"),
    retention_tag: RetentionTag = Form(RetentionTag.STANDARD),
    use_case_id: str | None = Form(None),
    evaluation_run_id: str | None = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Upload an evidence artifact with content-addressed storage.
    Computes SHA-256, stores in MinIO, records in DB with hash chain.
    """
    content = await file.read()

    # Get the latest artifact in the chain for this use case
    previous_artifact = None
    if use_case_id:
        result = await db.execute(
            select(EvidenceArtifact)
            .where(EvidenceArtifact.use_case_id == use_case_id)
            .order_by(EvidenceArtifact.created_at.desc())
            .limit(1)
        )
        previous_artifact = result.scalar_one_or_none()

    # Create the artifact record
    artifact = create_evidence_artifact(
        content=content,
        name=name,
        artifact_type=artifact_type,
        content_type=content_type,
        retention_tag=retention_tag,
        use_case_id=use_case_id,
        evaluation_run_id=evaluation_run_id,
        previous_artifact=previous_artifact,
        created_by=user.username,
    )

    # Upload to MinIO
    uploaded = await storage_client.upload(
        bucket=artifact.storage_bucket,
        key=artifact.storage_key,
        data=content,
        content_type=content_type,
    )
    if not uploaded:
        # Still save the record; storage can be retried
        artifact.metadata_extra = {"storage_pending": True}

    db.add(artifact)
    await db.flush()
    await db.refresh(artifact)

    # Emit audit event
    await emit_evidence_stored(artifact.id, artifact_type.value, artifact.content_hash)

    return EvidenceResponse.model_validate(artifact)


@router.get("/{artifact_id}", response_model=EvidenceResponse)
async def get_evidence(
    artifact_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    artifact = await db.get(EvidenceArtifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Evidence artifact not found")
    return EvidenceResponse.model_validate(artifact)


@router.get("/{artifact_id}/verify")
async def verify_evidence_integrity(
    artifact_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Verify tamper-evidence: re-download from storage, re-compute SHA-256,
    compare to stored hash. Also verifies hash chain integrity.
    """
    artifact = await db.get(EvidenceArtifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Evidence artifact not found")

    # Attempt to verify against actual storage
    storage_result = await storage_client.verify_integrity(
        bucket=artifact.storage_bucket,
        key=artifact.storage_key,
        expected_hash=artifact.content_hash,
    )

    # Verify hash chain link
    chain_valid = True
    if artifact.previous_artifact_id:
        prev = await db.get(EvidenceArtifact, artifact.previous_artifact_id)
        if prev:
            from app.services.evidence import compute_chain_hash

            expected_chain = compute_chain_hash(artifact.content_hash, prev.chain_hash)
            chain_valid = expected_chain == artifact.chain_hash

    return {
        "artifact_id": artifact.id,
        "content_hash": artifact.content_hash,
        "chain_hash": artifact.chain_hash,
        "worm_locked": artifact.worm_locked,
        "storage_verified": storage_result.get("verified"),
        "chain_verified": chain_valid,
        "integrity_status": (
            "verified"
            if storage_result.get("verified") and chain_valid
            else "storage_unavailable"
            if not storage_result.get("verified") and chain_valid
            else "integrity_failure"
        ),
        "verification_details": storage_result,
    }


@router.get("/{artifact_id}/download")
async def download_evidence(
    artifact_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Generate a presigned URL for secure artifact download."""
    artifact = await db.get(EvidenceArtifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Evidence artifact not found")

    url = await storage_client.get_presigned_url(
        bucket=artifact.storage_bucket,
        key=artifact.storage_key,
    )
    if url is None:
        raise HTTPException(status_code=503, detail="Storage service unavailable")

    return {"download_url": url, "expires_in_seconds": 3600}
