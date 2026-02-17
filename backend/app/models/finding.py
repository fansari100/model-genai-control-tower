"""Finding entity – issues discovered during evaluation or monitoring."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import AuditMixin, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.genai_use_case import GenAIUseCase


class FindingSeverity(enum.StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class FindingStatus(enum.StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    MITIGATED = "mitigated"
    ACCEPTED = "accepted"
    CLOSED = "closed"
    REOPENED = "reopened"


class FindingSource(enum.StrEnum):
    EVALUATION = "evaluation"
    RED_TEAM = "red_team"
    MONITORING = "monitoring"
    MANUAL = "manual"
    AUDIT = "audit"
    REGULATORY = "regulatory"
    INCIDENT = "incident"


class Finding(Base, TimestampMixin, AuditMixin):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    severity: Mapped[FindingSeverity] = mapped_column(
        SAEnum(FindingSeverity, name="finding_severity", native_enum=False),
        nullable=False,
    )
    status: Mapped[FindingStatus] = mapped_column(
        SAEnum(FindingStatus, name="finding_status", native_enum=False),
        default=FindingStatus.OPEN,
    )
    source: Mapped[FindingSource] = mapped_column(
        SAEnum(FindingSource, name="finding_source", native_enum=False),
        nullable=False,
    )

    # Links
    use_case_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("genai_use_cases.id"))
    evaluation_run_id: Mapped[str | None] = mapped_column(String(36))
    model_id: Mapped[str | None] = mapped_column(String(36))
    tool_id: Mapped[str | None] = mapped_column(String(36))

    # OWASP / framework mapping
    owasp_risk_id: Mapped[str | None] = mapped_column(String(50))
    mitre_atlas_technique: Mapped[str | None] = mapped_column(String(100))
    nist_consideration: Mapped[str | None] = mapped_column(String(100))

    # Evidence
    evidence_description: Mapped[str | None] = mapped_column(Text)
    evidence_artifact_ids: Mapped[list | None] = mapped_column(JSONB, default=list)

    # Remediation
    remediation_owner: Mapped[str | None] = mapped_column(String(255))
    remediation_plan: Mapped[str | None] = mapped_column(Text)
    remediation_due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    remediation_completed_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Relationships
    use_case: Mapped[GenAIUseCase | None] = relationship(back_populates="findings")

    def __repr__(self) -> str:
        return f"<Finding id={self.id} severity={self.severity} status={self.status}>"
