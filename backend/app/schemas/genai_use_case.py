"""GenAI Use Case schemas – intake, response, risk assessment."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.genai_use_case import (
    DataClassification,
    RiskRating,
    UseCaseCategory,
    UseCaseStatus,
)


class UseCaseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    version: str = "1.0.0"
    description: str | None = None
    business_justification: str | None = None
    category: UseCaseCategory
    data_classification: DataClassification = DataClassification.INTERNAL
    handles_pii: bool = False
    client_facing: bool = False
    uses_rag: bool = False
    uses_agents: bool = False
    uses_tools: bool = False
    uses_memory: bool = False
    requires_human_in_loop: bool = True
    owner: str = Field(..., min_length=1, max_length=255)
    business_unit: str | None = None
    sponsor: str | None = None
    committee_path: str | None = None
    metadata_extra: dict | None = None


class UseCaseCreate(UseCaseBase):
    model_ids: list[str] | None = None
    tool_ids: list[str] | None = None


class UseCaseUpdate(BaseModel):
    name: str | None = None
    version: str | None = None
    description: str | None = None
    business_justification: str | None = None
    category: UseCaseCategory | None = None
    status: UseCaseStatus | None = None
    risk_rating: RiskRating | None = None
    data_classification: DataClassification | None = None
    handles_pii: bool | None = None
    client_facing: bool | None = None
    uses_rag: bool | None = None
    uses_agents: bool | None = None
    uses_tools: bool | None = None
    uses_memory: bool | None = None
    requires_human_in_loop: bool | None = None
    owner: str | None = None
    business_unit: str | None = None
    sponsor: str | None = None
    committee_path: str | None = None
    guardrail_config: dict | None = None
    metadata_extra: dict | None = None


class UseCaseResponse(UseCaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: UseCaseStatus
    risk_rating: RiskRating
    required_test_suites: list | None = None
    guardrail_config: dict | None = None
    nist_governance_controls: dict | None = None
    nist_content_provenance: dict | None = None
    nist_predeployment_testing: dict | None = None
    nist_incident_disclosure: dict | None = None
    owasp_llm_top10_risks: dict | None = None
    owasp_agentic_top10_risks: dict | None = None
    iso42001_phase: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None


class UseCaseListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    version: str
    category: UseCaseCategory
    status: UseCaseStatus
    risk_rating: RiskRating
    data_classification: DataClassification
    client_facing: bool
    uses_agents: bool
    owner: str
    created_at: datetime | None = None


class UseCaseIntakeRequest(BaseModel):
    """Stage 0 intake form – generates risk rating + required test suites."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str
    category: UseCaseCategory
    owner: str
    business_unit: str | None = None
    sponsor: str | None = None

    # Model / provider list
    model_ids: list[str] | None = None
    model_descriptions: list[str] | None = None

    # Data classification
    data_classification: DataClassification = DataClassification.INTERNAL
    handles_pii: bool = False
    client_facing: bool = False

    # Architecture flags
    uses_rag: bool = False
    uses_agents: bool = False
    uses_tools: bool = False
    uses_memory: bool = False
    tool_ids: list[str] | None = None


class UseCaseIntakeResponse(BaseModel):
    """Result of intake triage – risk rating + required actions."""

    use_case_id: str
    risk_rating: RiskRating
    risk_score: float
    risk_factors: list[dict]
    required_test_suites: list[str]
    required_approvals: list[str]
    committee_path: str
    nist_considerations: dict
    owasp_llm_risks: list[str]
    owasp_agentic_risks: list[str]
    estimated_certification_days: int
