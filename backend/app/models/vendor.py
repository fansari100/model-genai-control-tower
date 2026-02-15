"""Vendor entity – tracks third-party model / service providers."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.model import Model


class VendorSecurityPosture(enum.StrEnum):
    APPROVED = "approved"
    CONDITIONAL = "conditional"
    UNDER_REVIEW = "under_review"
    REJECTED = "rejected"


class Vendor(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    legal_entity: Mapped[str | None] = mapped_column(String(255))
    contract_id: Mapped[str | None] = mapped_column(String(100))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)

    # Security & compliance posture
    security_posture: Mapped[VendorSecurityPosture] = mapped_column(
        SAEnum(VendorSecurityPosture, name="vendor_security_posture"),
        default=VendorSecurityPosture.UNDER_REVIEW,
    )
    sla_summary: Mapped[str | None] = mapped_column(Text)
    data_processing_region: Mapped[str | None] = mapped_column(String(100))
    certifications: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    # e.g. {"soc2": true, "iso27001": true, "fedramp": false}

    # Red-team due diligence (OWASP vendor eval criteria)
    redteam_due_diligence: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    # e.g. {"threat_model_coverage": "high", "eval_rigor": "medium", ...}

    # Relationships
    models: Mapped[list[Model]] = relationship(back_populates="vendor", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Vendor id={self.id} name={self.name}>"


# Avoid circular import – used only for type hints
