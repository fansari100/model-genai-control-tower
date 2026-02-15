"""Evidence artifact entity – immutable, content-addressed, audit-grade storage."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import AuditMixin, TimestampMixin, generate_uuid


class ArtifactType(enum.StrEnum):
    TEST_PLAN = "test_plan"
    TEST_RESULTS = "test_results"
    FINDINGS_REGISTER = "findings_register"
    APPROVAL_RECORD = "approval_record"
    MONITORING_PLAN = "monitoring_plan"
    MONITORING_REPORT = "monitoring_report"
    TRACE_EXPORT = "trace_export"
    PROMPT_OUTPUT_LOG = "prompt_output_log"
    AIBOM = "aibom"
    CERTIFICATION_PACK = "certification_pack"
    RED_TEAM_REPORT = "red_team_report"
    VULNERABILITY_SCAN = "vulnerability_scan"
    COMMITTEE_REPORT = "committee_report"
    ATTESTATION = "attestation"
    POLICY_BUNDLE = "policy_bundle"
    DATASET_SNAPSHOT = "dataset_snapshot"
    OTHER = "other"


class RetentionTag(enum.StrEnum):
    STANDARD = "standard"  # 3 years
    REGULATORY = "regulatory"  # 7 years
    PERMANENT = "permanent"  # indefinite


class EvidenceArtifact(Base, TimestampMixin, AuditMixin):
    """
    Immutable, content-addressed evidence artifact.
    Every certification/eval/approval produces evidence stored here.
    """

    __tablename__ = "evidence_artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    artifact_type: Mapped[ArtifactType] = mapped_column(
        SAEnum(ArtifactType, name="artifact_type"),
        nullable=False,
    )

    # Content-addressed storage
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    # SHA-256 of the artifact content
    hash_algorithm: Mapped[str] = mapped_column(String(20), default="sha256")

    # Storage location
    storage_bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), default="application/json")
    size_bytes: Mapped[int | None] = mapped_column(Integer)

    # WORM compliance
    retention_tag: Mapped[RetentionTag] = mapped_column(
        SAEnum(RetentionTag, name="retention_tag"),
        default=RetentionTag.STANDARD,
    )
    retention_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    worm_locked: Mapped[bool | None] = mapped_column(default=False)

    # Hash chain (for tamper evidence)
    previous_artifact_id: Mapped[str | None] = mapped_column(String(36))
    chain_hash: Mapped[str | None] = mapped_column(String(64))
    # chain_hash = SHA-256(content_hash + previous_chain_hash)

    # Linked entities
    use_case_id: Mapped[str | None] = mapped_column(String(36))
    evaluation_run_id: Mapped[str | None] = mapped_column(String(36))
    approval_id: Mapped[str | None] = mapped_column(String(36))

    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    def __repr__(self) -> str:
        return f"<EvidenceArtifact id={self.id} type={self.artifact_type} hash={self.content_hash[:12]}>"
