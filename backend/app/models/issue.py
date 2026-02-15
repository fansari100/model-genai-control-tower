"""Issue entity – audit/regulatory/internal issues linked to findings."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import AuditMixin, TimestampMixin, generate_uuid


class IssueSource(enum.StrEnum):
    INTERNAL = "internal"
    AUDIT = "audit"
    REGULATORY = "regulatory"
    INCIDENT = "incident"
    MONITORING = "monitoring"


class IssueStatus(enum.StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REMEDIATION = "remediation"
    VALIDATION = "validation"
    CLOSED = "closed"
    OVERDUE = "overdue"


class IssuePriority(enum.StrEnum):
    P1_CRITICAL = "p1_critical"
    P2_HIGH = "p2_high"
    P3_MEDIUM = "p3_medium"
    P4_LOW = "p4_low"


class Issue(Base, TimestampMixin, AuditMixin):
    __tablename__ = "issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    source: Mapped[IssueSource] = mapped_column(
        SAEnum(IssueSource, name="issue_source", native_enum=False),
        nullable=False,
    )
    status: Mapped[IssueStatus] = mapped_column(
        SAEnum(IssueStatus, name="issue_status", native_enum=False),
        default=IssueStatus.OPEN,
    )
    priority: Mapped[IssuePriority] = mapped_column(
        SAEnum(IssuePriority, name="issue_priority", native_enum=False),
        default=IssuePriority.P3_MEDIUM,
    )

    # Links
    use_case_id: Mapped[str | None] = mapped_column(String(36))
    finding_ids: Mapped[list | None] = mapped_column(JSONB, default=list)

    # Ownership
    owner: Mapped[str | None] = mapped_column(String(255))
    assignee: Mapped[str | None] = mapped_column(String(255))

    # Dates
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # NIST incident disclosure
    incident_disclosure: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    # e.g. {"disclosed_to": ["risk_committee"], "disclosure_date": "...", "regulatory_notification": false}

    # Remediation tracking
    remediation_plan: Mapped[str | None] = mapped_column(Text)
    evidence_artifact_ids: Mapped[list | None] = mapped_column(JSONB, default=list)

    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    def __repr__(self) -> str:
        return f"<Issue id={self.id} priority={self.priority} status={self.status}>"
