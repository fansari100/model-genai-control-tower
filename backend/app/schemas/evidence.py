"""Evidence artifact schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.evidence import ArtifactType, RetentionTag


class EvidenceCreate(BaseModel):
    name: str
    description: str | None = None
    artifact_type: ArtifactType
    content_type: str = "application/json"
    retention_tag: RetentionTag = RetentionTag.STANDARD
    use_case_id: str | None = None
    evaluation_run_id: str | None = None
    approval_id: str | None = None
    metadata_extra: dict | None = None


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    artifact_type: ArtifactType
    content_hash: str
    hash_algorithm: str
    storage_bucket: str
    storage_key: str
    content_type: str
    size_bytes: int | None = None
    retention_tag: RetentionTag
    retention_until: datetime | None = None
    worm_locked: bool | None = None
    previous_artifact_id: str | None = None
    chain_hash: str | None = None
    use_case_id: str | None = None
    evaluation_run_id: str | None = None
    approval_id: str | None = None
    created_at: datetime | None = None
    created_by: str | None = None


class CertificationPackRequest(BaseModel):
    """Request to generate a complete certification evidence pack."""

    use_case_id: str
    include_test_plan: bool = True
    include_test_results: bool = True
    include_findings: bool = True
    include_approvals: bool = True
    include_monitoring_plan: bool = True
    include_trace_export: bool = True
    include_prompt_logs: bool = True
    include_aibom: bool = True
    output_format: str = "pdf"  # pdf, json, both


class CertificationPackResponse(BaseModel):
    pack_id: str
    use_case_id: str
    use_case_name: str
    generated_at: datetime
    artifact_ids: list[str]
    sections: list[dict]
    overall_status: str
    risk_rating: str
    summary: dict
