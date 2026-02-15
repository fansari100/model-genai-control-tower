"""Model schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from app.models.model import ModelDeployment, ModelStatus, ModelType, RiskTier

if TYPE_CHECKING:
    from datetime import datetime


class ModelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    version: str = "1.0.0"
    description: str | None = None
    purpose: str | None = None
    model_type: ModelType
    deployment: ModelDeployment = ModelDeployment.VENDOR_API
    risk_tier: RiskTier = RiskTier.TIER_3_MEDIUM
    owner: str = Field(..., min_length=1, max_length=255)
    business_unit: str | None = None
    committee_path: str | None = None
    provider_model_id: str | None = None
    parameter_count: int | None = None
    context_window: int | None = None
    training_cutoff: str | None = None
    inputs_description: str | None = None
    outputs_description: str | None = None
    known_limitations: str | None = None
    vendor_id: str | None = None
    sr_11_7_classification: str | None = None
    nist_genai_considerations: dict | None = None
    owasp_llm_risks: dict | None = None
    mitre_atlas_techniques: list | None = None
    metadata_extra: dict | None = None


class ModelCreate(ModelBase):
    pass


class ModelUpdate(BaseModel):
    name: str | None = None
    version: str | None = None
    description: str | None = None
    purpose: str | None = None
    model_type: ModelType | None = None
    deployment: ModelDeployment | None = None
    status: ModelStatus | None = None
    risk_tier: RiskTier | None = None
    owner: str | None = None
    business_unit: str | None = None
    provider_model_id: str | None = None
    known_limitations: str | None = None
    vendor_id: str | None = None
    metadata_extra: dict | None = None


class ModelResponse(ModelBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: ModelStatus
    aibom_artifact_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None


class ModelListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    version: str
    model_type: ModelType
    deployment: ModelDeployment
    status: ModelStatus
    risk_tier: RiskTier
    owner: str
    vendor_id: str | None = None
    created_at: datetime | None = None
