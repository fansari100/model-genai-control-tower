"""Tests for the evidence service."""

from __future__ import annotations

from app.models.evidence import ArtifactType, RetentionTag
from app.services.evidence import (
    compute_chain_hash,
    compute_content_hash,
    create_evidence_artifact,
    serialize_for_evidence,
    verify_chain_integrity,
)


def test_content_hash_deterministic():
    """Same content should produce same hash."""
    data = b"test content"
    h1 = compute_content_hash(data)
    h2 = compute_content_hash(data)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex length


def test_content_hash_different():
    """Different content should produce different hashes."""
    h1 = compute_content_hash(b"content a")
    h2 = compute_content_hash(b"content b")
    assert h1 != h2


def test_chain_hash():
    """Chain hash should combine content hash with previous chain."""
    ch1 = compute_chain_hash("abc123", None)
    ch2 = compute_chain_hash("abc123", "prev_chain_456")
    assert ch1 != ch2  # Different previous chain → different result
    assert len(ch1) == 64


def test_create_evidence_artifact():
    """Create an evidence artifact with proper hashing."""
    content = serialize_for_evidence({"test": "data", "score": 0.95})
    artifact = create_evidence_artifact(
        content=content,
        name="test_artifact",
        artifact_type=ArtifactType.TEST_RESULTS,
        use_case_id="uc-123",
    )
    assert artifact.content_hash is not None
    assert artifact.chain_hash is not None
    assert artifact.storage_key.startswith("evidence/uc-123/")
    assert artifact.size_bytes == len(content)


def test_chain_integrity_valid():
    """Valid chain should pass verification."""
    content1 = b"first artifact"
    art1 = create_evidence_artifact(
        content=content1,
        name="art1",
        artifact_type=ArtifactType.TEST_PLAN,
    )
    content2 = b"second artifact"
    art2 = create_evidence_artifact(
        content=content2,
        name="art2",
        artifact_type=ArtifactType.TEST_RESULTS,
        previous_artifact=art1,
    )

    report = verify_chain_integrity([art1, art2])
    assert report["is_valid"] is True
    assert report["chain_length"] == 2
