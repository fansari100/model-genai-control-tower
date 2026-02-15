"""Approval schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from datetime import datetime

    from app.models.approval import ApprovalDecision, ApprovalGateType


class ApprovalCreate(BaseModel):
    gate_type: ApprovalGateType
    decision: ApprovalDecision
    approver_role: str = Field(..., min_length=1, max_length=100)
    approver_name: str = Field(..., min_length=1, max_length=255)
    approver_email: str | None = None
    rationale: str | None = None
    conditions: list | None = None
    use_case_id: str | None = None
    model_id: str | None = None
    tool_id: str | None = None
    evidence_artifact_ids: list | None = None


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    gate_type: ApprovalGateType
    decision: ApprovalDecision
    approver_role: str
    approver_name: str
    approver_email: str | None = None
    rationale: str | None = None
    conditions: list | None = None
    use_case_id: str | None = None
    model_id: str | None = None
    tool_id: str | None = None
    policy_input: dict | None = None
    policy_output: dict | None = None
    decision_hash: str | None = None
    created_at: datetime | None = None
