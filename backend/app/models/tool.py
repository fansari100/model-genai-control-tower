"""Tool / EUC entity – non-model tools, spreadsheets, calculators under governance."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, String, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin, AuditMixin, generate_uuid


class ToolCategory(str, enum.Enum):
    EUC_SPREADSHEET = "euc_spreadsheet"
    EUC_VBA = "euc_vba"
    SYSTEM_CALCULATOR = "system_calculator"
    SCRIPT = "script"
    DASHBOARD = "dashboard"
    API_SERVICE = "api_service"
    AGENT_TOOL = "agent_tool"
    DATABASE_QUERY = "database_query"
    OTHER = "other"


class ToolCriticality(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ToolStatus(str, enum.Enum):
    ACTIVE = "active"
    UNDER_REVIEW = "under_review"
    ATTESTED = "attested"
    ATTESTATION_DUE = "attestation_due"
    ATTESTATION_OVERDUE = "attestation_overdue"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class Tool(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    Represents a non-model tool / EUC under governance.
    Mirrors the firm's tool DB concept (e.g. ClusterSeven IMS).
    """

    __tablename__ = "tools"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    description: Mapped[str | None] = mapped_column(Text)
    purpose: Mapped[str | None] = mapped_column(Text)

    category: Mapped[ToolCategory] = mapped_column(
        SAEnum(ToolCategory, name="tool_category"),
        nullable=False,
    )
    criticality: Mapped[ToolCriticality] = mapped_column(
        SAEnum(ToolCriticality, name="tool_criticality"),
        default=ToolCriticality.MEDIUM,
    )
    status: Mapped[ToolStatus] = mapped_column(
        SAEnum(ToolStatus, name="tool_status"),
        default=ToolStatus.UNDER_REVIEW,
    )

    # Ownership
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    business_unit: Mapped[str | None] = mapped_column(String(100))
    custodian: Mapped[str | None] = mapped_column(String(255))

    # Technical
    technology_stack: Mapped[str | None] = mapped_column(String(255))
    location_path: Mapped[str | None] = mapped_column(String(500))
    # e.g. "\\sharepoint\wm-tools\calculator_v3.xlsm"
    inputs_description: Mapped[str | None] = mapped_column(Text)
    outputs_description: Mapped[str | None] = mapped_column(Text)
    upstream_dependencies: Mapped[list | None] = mapped_column(JSONB, default=list)
    downstream_consumers: Mapped[list | None] = mapped_column(JSONB, default=list)

    # Attestation
    last_attestation_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_attestation_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attestation_frequency_days: Mapped[int | None] = mapped_column(default=365)
    attestation_owner: Mapped[str | None] = mapped_column(String(255))

    # For agent tools: security controls
    agent_tool_config: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    # e.g. {"allowlisted": true, "argument_schema": {...}, "requires_approval": false, "sandboxed": true}

    # Metadata
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Relationships
    use_case_links: Mapped[list["UseCaseToolLink"]] = relationship(
        back_populates="tool", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Tool id={self.id} name={self.name} category={self.category}>"


from app.models.genai_use_case import UseCaseToolLink  # noqa: E402
