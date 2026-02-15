"""Approval entity – governance gate decisions."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import AuditMixin, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.genai_use_case import GenAIUseCase


class ApprovalDecision(enum.StrEnum):
    APPROVED = "approved"
    CONDITIONAL = "conditional"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    DEFERRED = "deferred"


class ApprovalGateType(enum.StrEnum):
    INTAKE_TRIAGE = "intake_triage"
    RISK_ASSESSMENT = "risk_assessment"
    PRE_DEPLOYMENT = "pre_deployment"
    PRODUCTION_RELEASE = "production_release"
    RECERTIFICATION = "recertification"
    TOOL_ATTESTATION = "tool_attestation"
    EXCEPTION = "exception"


class Approval(Base, TimestampMixin, AuditMixin):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    gate_type: Mapped[ApprovalGateType] = mapped_column(
        SAEnum(ApprovalGateType, name="approval_gate_type"),
        nullable=False,
    )
    decision: Mapped[ApprovalDecision] = mapped_column(
        SAEnum(ApprovalDecision, name="approval_decision"),
        nullable=False,
    )

    # Who decided
    approver_role: Mapped[str] = mapped_column(String(100), nullable=False)
    approver_name: Mapped[str] = mapped_column(String(255), nullable=False)
    approver_email: Mapped[str | None] = mapped_column(String(255))

    # Rationale (critical for audit trail)
    rationale: Mapped[str | None] = mapped_column(Text)
    conditions: Mapped[list | None] = mapped_column(JSONB, default=list)
    # e.g. ["Must complete additional PII testing", "Quarterly recertification required"]

    # Policy engine inputs/outputs
    policy_input: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    policy_output: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Links
    use_case_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("genai_use_cases.id"))
    model_id: Mapped[str | None] = mapped_column(String(36))
    tool_id: Mapped[str | None] = mapped_column(String(36))

    # Evidence
    evidence_artifact_ids: Mapped[list | None] = mapped_column(JSONB, default=list)

    # Digital signature (hash of decision record for tamper evidence)
    decision_hash: Mapped[str | None] = mapped_column(String(64))

    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Relationships
    use_case: Mapped[GenAIUseCase | None] = relationship(back_populates="approvals")

    def __repr__(self) -> str:
        return f"<Approval id={self.id} gate={self.gate_type} decision={self.decision}>"
