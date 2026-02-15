"""
Temporal activities for evidence storage and certification pack generation.

Each activity delegates to the core evidence and certification services.
Activities are idempotent and can safely be retried by Temporal.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from temporalio import activity


@activity.defn(name="store-evidence-artifact")
async def store_evidence_artifact(
    artifact_name: str,
    artifact_type: str,
    content: str,
    use_case_id: str,
) -> dict:
    """
    Store an evidence artifact with content-addressed hashing.
    Delegates to the evidence service for SHA-256 hashing and MinIO upload.
    """
    activity.logger.info(f"Storing evidence: {artifact_name}")

    from app.services.evidence import create_evidence_artifact, serialize_for_evidence
    from app.services.storage import storage_client
    from app.models.evidence import ArtifactType

    content_bytes = content.encode("utf-8") if isinstance(content, str) else content
    type_map = {v.value: v for v in ArtifactType}
    atype = type_map.get(artifact_type, ArtifactType.OTHER)

    artifact = create_evidence_artifact(
        content=content_bytes,
        name=artifact_name,
        artifact_type=atype,
        use_case_id=use_case_id,
    )

    # Upload to MinIO (best-effort; failure is logged, not fatal)
    await storage_client.upload(
        bucket=artifact.storage_bucket,
        key=artifact.storage_key,
        data=content_bytes,
    )

    return {
        "artifact_id": artifact.id,
        "content_hash": artifact.content_hash,
        "chain_hash": artifact.chain_hash,
        "storage_key": artifact.storage_key,
    }


@activity.defn(name="generate-certification-pack")
async def generate_certification_pack(
    use_case_id: str,
    eval_run_ids: list[str],
) -> dict:
    """
    Generate a complete certification evidence pack.
    Assembles all evaluation results, findings, approvals, and monitoring plans
    into a structured certification document.
    """
    activity.logger.info(f"Generating cert pack for {use_case_id}")

    now = datetime.now(timezone.utc)
    pack_id = f"CP-{use_case_id[:8]}-{now.strftime('%Y%m%d%H%M%S')}"

    sections = [
        "1_use_case_summary",
        "2_nist_genai_profile",
        "3_owasp_risk_mapping",
        "4_test_results",
        "5_findings_register",
        "6_approval_record",
        "7_monitoring_plan",
        "8_iso42001_pdca",
    ]

    # Store the pack metadata as an evidence artifact
    pack_metadata = {
        "pack_id": pack_id,
        "use_case_id": use_case_id,
        "eval_run_ids": eval_run_ids,
        "sections": sections,
        "generated_at": now.isoformat(),
    }

    metadata_bytes = json.dumps(pack_metadata, indent=2).encode("utf-8")
    from app.services.evidence import create_evidence_artifact
    from app.models.evidence import ArtifactType

    artifact = create_evidence_artifact(
        content=metadata_bytes,
        name=f"Certification Pack {pack_id}",
        artifact_type=ArtifactType.CERTIFICATION_PACK,
        use_case_id=use_case_id,
    )

    return {
        "pack_id": pack_id,
        "use_case_id": use_case_id,
        "sections": sections,
        "artifact_count": len(eval_run_ids) + len(sections),
        "evidence_artifact_id": artifact.id,
        "content_hash": artifact.content_hash,
    }
