"""Vendor schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.vendor import VendorSecurityPosture


class VendorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    legal_entity: str | None = None
    contract_id: str | None = None
    contact_email: str | None = None
    description: str | None = None
    security_posture: VendorSecurityPosture = VendorSecurityPosture.UNDER_REVIEW
    sla_summary: str | None = None
    data_processing_region: str | None = None
    certifications: dict | None = None
    redteam_due_diligence: dict | None = None


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: str | None = None
    legal_entity: str | None = None
    contract_id: str | None = None
    contact_email: str | None = None
    description: str | None = None
    security_posture: VendorSecurityPosture | None = None
    sla_summary: str | None = None
    data_processing_region: str | None = None
    certifications: dict | None = None
    redteam_due_diligence: dict | None = None


class VendorResponse(VendorBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None
    model_count: int = 0


class VendorListResponse(VendorResponse):
    pass
