"""
Evidence service – content-addressed artifact storage with hash chain.

Implements:
- SHA-256 content addressing
- Hash chain for tamper evidence
- MinIO / S3 storage with WORM option
- Retention policy enforcement
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from app.models.evidence import ArtifactType, EvidenceArtifact, RetentionTag

logger = structlog.get_logger()

# Retention durations
RETENTION_DURATIONS = {
    RetentionTag.STANDARD: timedelta(days=3 * 365),
    RetentionTag.REGULATORY: timedelta(days=7 * 365),
    RetentionTag.PERMANENT: timedelta(days=100 * 365),
}


def compute_content_hash(content: bytes) -> str:
    """Compute SHA-256 hash of content."""
    return hashlib.sha256(content).hexdigest()


def compute_chain_hash(content_hash: str, previous_chain_hash: str | None) -> str:
    """Compute hash chain: SHA-256(content_hash + previous_chain_hash)."""
    chain_input = content_hash + (previous_chain_hash or "genesis")
    return hashlib.sha256(chain_input.encode()).hexdigest()


def build_storage_key(
    artifact_type: ArtifactType,
    use_case_id: str | None,
    artifact_id: str,
    content_type: str,
) -> str:
    """Build a structured S3/MinIO key for the artifact."""
    ext_map = {
        "application/json": "json",
        "application/pdf": "pdf",
        "text/plain": "txt",
        "text/csv": "csv",
    }
    ext = ext_map.get(content_type, "bin")
    prefix = use_case_id or "global"
    return f"evidence/{prefix}/{artifact_type.value}/{artifact_id}.{ext}"


def create_evidence_artifact(
    content: bytes,
    name: str,
    artifact_type: ArtifactType,
    content_type: str = "application/json",
    retention_tag: RetentionTag = RetentionTag.STANDARD,
    use_case_id: str | None = None,
    evaluation_run_id: str | None = None,
    approval_id: str | None = None,
    previous_artifact: EvidenceArtifact | None = None,
    bucket: str = "ct-evidence",
    created_by: str = "system",
) -> EvidenceArtifact:
    """
    Create a new evidence artifact with content-addressed storage
    and hash chain linking.
    """
    from app.models.base import generate_uuid

    artifact_id = generate_uuid()
    content_hash = compute_content_hash(content)

    previous_chain_hash = previous_artifact.chain_hash if previous_artifact else None
    chain_hash = compute_chain_hash(content_hash, previous_chain_hash)

    now = datetime.now(timezone.utc)
    retention_until = now + RETENTION_DURATIONS[retention_tag]

    storage_key = build_storage_key(artifact_type, use_case_id, artifact_id, content_type)

    artifact = EvidenceArtifact(
        id=artifact_id,
        name=name,
        artifact_type=artifact_type,
        content_hash=content_hash,
        hash_algorithm="sha256",
        storage_bucket=bucket,
        storage_key=storage_key,
        content_type=content_type,
        size_bytes=len(content),
        retention_tag=retention_tag,
        retention_until=retention_until,
        worm_locked=False,
        previous_artifact_id=previous_artifact.id if previous_artifact else None,
        chain_hash=chain_hash,
        use_case_id=use_case_id,
        evaluation_run_id=evaluation_run_id,
        approval_id=approval_id,
        created_by=created_by,
    )

    logger.info(
        "evidence_artifact_created",
        artifact_id=artifact_id,
        content_hash=content_hash[:16],
        chain_hash=chain_hash[:16],
        artifact_type=artifact_type.value,
    )

    return artifact


def verify_chain_integrity(artifacts: list[EvidenceArtifact]) -> dict:
    """
    Verify the hash chain integrity of a sequence of artifacts.
    Returns verification report.
    """
    results: list[dict] = []
    is_valid = True

    for i, artifact in enumerate(artifacts):
        expected_chain = compute_chain_hash(
            artifact.content_hash,
            artifacts[i - 1].chain_hash if i > 0 else None,
        )
        valid = expected_chain == artifact.chain_hash
        if not valid:
            is_valid = False

        results.append({
            "artifact_id": artifact.id,
            "position": i,
            "content_hash": artifact.content_hash,
            "chain_hash": artifact.chain_hash,
            "expected_chain_hash": expected_chain,
            "valid": valid,
        })

    return {
        "chain_length": len(artifacts),
        "is_valid": is_valid,
        "verification_results": results,
    }


def serialize_for_evidence(data: Any) -> bytes:
    """Serialize data to JSON bytes for evidence storage."""
    return json.dumps(data, indent=2, default=str, sort_keys=True).encode("utf-8")
