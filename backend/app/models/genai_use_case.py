"""GenAI Use Case entity – a governed AI/GenAI application or workflow."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from app.models.approval import Approval
    from app.models.evaluation import EvaluationRun
    from app.models.finding import Finding
    from app.models.model import Model
    from app.models.monitoring import MonitoringPlan
    from app.models.tool import Tool


class UseCaseCategory(enum.StrEnum):
    RAG_QA = "rag_qa"
    SUMMARIZATION = "summarization"
    CONTENT_GENERATION = "content_generation"
    DATA_EXTRACTION = "data_extraction"
    CODE_GENERATION = "code_generation"
    AGENT_WORKFLOW = "agent_workflow"
    CLASSIFICATION = "classification"
    TRANSLATION = "translation"
    OTHER = "other"


class DataClassification(enum.StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    PII = "pii"
    RESTRICTED = "restricted"


class UseCaseStatus(enum.StrEnum):
    DRAFT = "draft"
    INTAKE = "intake"
    RISK_ASSESSMENT = "risk_assessment"
    TESTING = "testing"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    CONDITIONAL = "conditional"
    MONITORING = "monitoring"
    RECERTIFICATION = "recertification"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class RiskRating(enum.StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class GenAIUseCase(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    A governed GenAI application / workflow.
    Examples: meeting summarizer, internal Q&A assistant, agent-based research.
    """

    __tablename__ = "genai_use_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    description: Mapped[str | None] = mapped_column(Text)
    business_justification: Mapped[str | None] = mapped_column(Text)

    category: Mapped[UseCaseCategory] = mapped_column(
        SAEnum(UseCaseCategory, name="use_case_category"),
        nullable=False,
    )
    status: Mapped[UseCaseStatus] = mapped_column(
        SAEnum(UseCaseStatus, name="use_case_status"),
        default=UseCaseStatus.DRAFT,
    )
    risk_rating: Mapped[RiskRating] = mapped_column(
        SAEnum(RiskRating, name="risk_rating"),
        default=RiskRating.MEDIUM,
    )

    # Data & privacy
    data_classification: Mapped[DataClassification] = mapped_column(
        SAEnum(DataClassification, name="data_classification"),
        default=DataClassification.INTERNAL,
    )
    handles_pii: Mapped[bool] = mapped_column(Boolean, default=False)
    client_facing: Mapped[bool] = mapped_column(Boolean, default=False)

    # Architecture flags
    uses_rag: Mapped[bool] = mapped_column(Boolean, default=False)
    uses_agents: Mapped[bool] = mapped_column(Boolean, default=False)
    uses_tools: Mapped[bool] = mapped_column(Boolean, default=False)
    uses_memory: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_human_in_loop: Mapped[bool] = mapped_column(Boolean, default=True)

    # Ownership
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    business_unit: Mapped[str | None] = mapped_column(String(100))
    sponsor: Mapped[str | None] = mapped_column(String(255))
    committee_path: Mapped[str | None] = mapped_column(String(255))

    # NIST GenAI Profile (AI 600-1) mapping
    nist_governance_controls: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    nist_content_provenance: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    nist_predeployment_testing: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    nist_incident_disclosure: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # OWASP mappings
    owasp_llm_top10_risks: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    owasp_agentic_top10_risks: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # ISO 42001 PDCA phase
    iso42001_phase: Mapped[str | None] = mapped_column(String(20))

    # Required test suites (auto-determined by risk rating)
    required_test_suites: Mapped[list | None] = mapped_column(JSONB, default=list)

    # Guardrail configuration
    guardrail_config: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    # e.g. {"cascade_stage1": "lightweight_filter", "cascade_stage2": "heavy_classifier", ...}

    # Metadata
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Relationships
    model_links: Mapped[list[UseCaseModelLink]] = relationship(
        back_populates="use_case", lazy="selectin", cascade="all, delete-orphan"
    )
    tool_links: Mapped[list[UseCaseToolLink]] = relationship(
        back_populates="use_case", lazy="selectin", cascade="all, delete-orphan"
    )
    evaluation_runs: Mapped[list[EvaluationRun]] = relationship(
        back_populates="use_case", lazy="selectin"
    )
    findings: Mapped[list[Finding]] = relationship(back_populates="use_case", lazy="selectin")
    approvals: Mapped[list[Approval]] = relationship(back_populates="use_case", lazy="selectin")
    monitoring_plans: Mapped[list[MonitoringPlan]] = relationship(
        back_populates="use_case", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<GenAIUseCase id={self.id} name={self.name} status={self.status}>"


class UseCaseModelLink(Base, TimestampMixin):
    """Association table: use case ↔ model (many-to-many with metadata)."""

    __tablename__ = "use_case_model_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    use_case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("genai_use_cases.id"), nullable=False
    )
    model_id: Mapped[str] = mapped_column(String(36), ForeignKey("models.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="primary")
    # e.g. "primary", "fallback", "evaluator", "classifier"
    configuration: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    use_case: Mapped[GenAIUseCase] = relationship(back_populates="model_links")
    model: Mapped[Model] = relationship(back_populates="use_case_links")


class UseCaseToolLink(Base, TimestampMixin):
    """Association table: use case ↔ tool (many-to-many with metadata)."""

    __tablename__ = "use_case_tool_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    use_case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("genai_use_cases.id"), nullable=False
    )
    tool_id: Mapped[str] = mapped_column(String(36), ForeignKey("tools.id"), nullable=False)
    purpose: Mapped[str | None] = mapped_column(String(255))
    permission_scope: Mapped[str | None] = mapped_column(String(100))
    requires_approval: Mapped[bool] = mapped_column(default=False)

    use_case: Mapped[GenAIUseCase] = relationship(back_populates="tool_links")
    tool: Mapped[Tool] = relationship(back_populates="use_case_links")
