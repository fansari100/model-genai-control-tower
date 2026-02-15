"""Model entity – statistical, ML, LLM, or vendor model under governance."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.evaluation import EvaluationRun
    from app.models.genai_use_case import UseCaseModelLink
    from app.models.vendor import Vendor


class ModelType(enum.StrEnum):
    STATISTICAL = "statistical"
    ML_TRADITIONAL = "ml_traditional"
    DEEP_LEARNING = "deep_learning"
    LLM = "llm"
    MULTIMODAL = "multimodal"
    ENSEMBLE = "ensemble"


class ModelDeployment(enum.StrEnum):
    VENDOR_API = "vendor_api"
    SELF_HOSTED = "self_hosted"
    ON_PREMISE = "on_premise"
    HYBRID = "hybrid"


class ModelStatus(enum.StrEnum):
    DRAFT = "draft"
    INTAKE = "intake"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    CONDITIONAL = "conditional"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class RiskTier(enum.StrEnum):
    TIER_1_CRITICAL = "tier_1_critical"
    TIER_2_HIGH = "tier_2_high"
    TIER_3_MEDIUM = "tier_3_medium"
    TIER_4_LOW = "tier_4_low"


class Model(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    description: Mapped[str | None] = mapped_column(Text)
    purpose: Mapped[str | None] = mapped_column(Text)

    model_type: Mapped[ModelType] = mapped_column(
        SAEnum(ModelType, name="model_type"),
        nullable=False,
    )
    deployment: Mapped[ModelDeployment] = mapped_column(
        SAEnum(ModelDeployment, name="model_deployment"),
        default=ModelDeployment.VENDOR_API,
    )
    status: Mapped[ModelStatus] = mapped_column(
        SAEnum(ModelStatus, name="model_status"),
        default=ModelStatus.DRAFT,
    )
    risk_tier: Mapped[RiskTier] = mapped_column(
        SAEnum(RiskTier, name="risk_tier"),
        default=RiskTier.TIER_3_MEDIUM,
    )

    # Ownership & organizational
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    business_unit: Mapped[str | None] = mapped_column(String(100))
    committee_path: Mapped[str | None] = mapped_column(String(255))

    # Technical details
    provider_model_id: Mapped[str | None] = mapped_column(String(255))
    # e.g. "gpt-4o-2024-11-20", "claude-sonnet-4-20250514"
    parameter_count: Mapped[int | None] = mapped_column(Integer)
    context_window: Mapped[int | None] = mapped_column(Integer)
    training_cutoff: Mapped[str | None] = mapped_column(String(50))

    # Inputs / Outputs / Limitations
    inputs_description: Mapped[str | None] = mapped_column(Text)
    outputs_description: Mapped[str | None] = mapped_column(Text)
    known_limitations: Mapped[str | None] = mapped_column(Text)

    # AIBOM reference
    aibom_artifact_id: Mapped[str | None] = mapped_column(String(36))

    # Compliance & framework mappings
    sr_11_7_classification: Mapped[str | None] = mapped_column(String(50))
    nist_genai_considerations: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    owasp_llm_risks: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    mitre_atlas_techniques: Mapped[list | None] = mapped_column(JSONB, default=list)

    # Metadata
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Foreign keys
    vendor_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("vendors.id"), nullable=True
    )

    # Relationships
    vendor: Mapped[Vendor | None] = relationship(back_populates="models", lazy="selectin")
    use_case_links: Mapped[list[UseCaseModelLink]] = relationship(
        back_populates="model", lazy="selectin"
    )
    evaluation_runs: Mapped[list[EvaluationRun]] = relationship(
        back_populates="model", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Model id={self.id} name={self.name} v{self.version}>"


# Resolve forward references for relationship type annotations
