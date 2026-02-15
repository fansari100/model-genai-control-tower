"""Finding schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from datetime import datetime

    from app.models.finding import FindingSeverity, FindingSource, FindingStatus


class FindingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    severity: FindingSeverity
    source: FindingSource
    use_case_id: str | None = None
    evaluation_run_id: str | None = None
    model_id: str | None = None
    tool_id: str | None = None
    owasp_risk_id: str | None = None
    mitre_atlas_technique: str | None = None
    nist_consideration: str | None = None
    evidence_description: str | None = None
    evidence_artifact_ids: list | None = None
    remediation_owner: str | None = None
    remediation_plan: str | None = None
    remediation_due_date: datetime | None = None


class FindingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: FindingSeverity | None = None
    status: FindingStatus | None = None
    remediation_owner: str | None = None
    remediation_plan: str | None = None
    remediation_due_date: datetime | None = None
    remediation_completed_date: datetime | None = None


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str | None = None
    severity: FindingSeverity
    status: FindingStatus
    source: FindingSource
    use_case_id: str | None = None
    evaluation_run_id: str | None = None
    owasp_risk_id: str | None = None
    mitre_atlas_technique: str | None = None
    nist_consideration: str | None = None
    evidence_description: str | None = None
    remediation_owner: str | None = None
    remediation_plan: str | None = None
    remediation_due_date: datetime | None = None
    remediation_completed_date: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
