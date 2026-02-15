"""Tool / EUC schemas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from app.models.tool import ToolCategory, ToolCriticality, ToolStatus

if TYPE_CHECKING:
    from datetime import datetime


class ToolBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    version: str = "1.0"
    description: str | None = None
    purpose: str | None = None
    category: ToolCategory
    criticality: ToolCriticality = ToolCriticality.MEDIUM
    owner: str = Field(..., min_length=1, max_length=255)
    business_unit: str | None = None
    custodian: str | None = None
    technology_stack: str | None = None
    location_path: str | None = None
    inputs_description: str | None = None
    outputs_description: str | None = None
    upstream_dependencies: list | None = None
    downstream_consumers: list | None = None
    attestation_frequency_days: int | None = 365
    attestation_owner: str | None = None
    agent_tool_config: dict | None = None
    metadata_extra: dict | None = None


class ToolCreate(ToolBase):
    pass


class ToolUpdate(BaseModel):
    name: str | None = None
    version: str | None = None
    description: str | None = None
    purpose: str | None = None
    category: ToolCategory | None = None
    criticality: ToolCriticality | None = None
    status: ToolStatus | None = None
    owner: str | None = None
    business_unit: str | None = None
    custodian: str | None = None
    technology_stack: str | None = None
    location_path: str | None = None
    attestation_frequency_days: int | None = None
    attestation_owner: str | None = None
    agent_tool_config: dict | None = None
    metadata_extra: dict | None = None


class ToolResponse(ToolBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: ToolStatus
    last_attestation_date: datetime | None = None
    next_attestation_date: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None


class ToolListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    version: str
    category: ToolCategory
    criticality: ToolCriticality
    status: ToolStatus
    owner: str
    last_attestation_date: datetime | None = None
    next_attestation_date: datetime | None = None
    created_at: datetime | None = None
