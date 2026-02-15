"""Monitoring entities – plans, executions, drift detection."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, AuditMixin, generate_uuid


class MonitoringCadence(str, enum.Enum):
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class MonitoringStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


class AlertSeverity(str, enum.Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class MonitoringPlan(Base, TimestampMixin, AuditMixin):
    """Defines what to monitor and how for a governed use case."""

    __tablename__ = "monitoring_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Link
    use_case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("genai_use_cases.id"), nullable=False
    )

    status: Mapped[MonitoringStatus] = mapped_column(
        SAEnum(MonitoringStatus, name="monitoring_status"),
        default=MonitoringStatus.ACTIVE,
    )
    cadence: Mapped[MonitoringCadence] = mapped_column(
        SAEnum(MonitoringCadence, name="monitoring_cadence"),
        default=MonitoringCadence.DAILY,
    )

    # Canary / regression config
    canary_prompts: Mapped[list | None] = mapped_column(JSONB, default=list)
    regression_dataset_id: Mapped[str | None] = mapped_column(String(36))

    # Thresholds
    thresholds: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    # e.g. {"faithfulness_min": 0.85, "toxicity_max": 0.05, "latency_p99_ms": 5000}

    # Alert routing
    alert_routing: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    # e.g. {"critical": ["slack:#ct-alerts", "email:team@"], "warning": ["slack:#ct-monitoring"]}

    # Recertification triggers
    recert_triggers: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    # e.g. {"model_version_change": true, "prompt_template_change": true, "corpus_change": true,
    #        "tool_permission_expand": true, "new_agent_capability": true}

    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Relationships
    use_case: Mapped["GenAIUseCase"] = relationship(back_populates="monitoring_plans")
    executions: Mapped[list["MonitoringExecution"]] = relationship(
        back_populates="plan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<MonitoringPlan id={self.id} cadence={self.cadence}>"


class MonitoringExecution(Base, TimestampMixin):
    """A single monitoring check execution."""

    __tablename__ = "monitoring_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("monitoring_plans.id"), nullable=False
    )

    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_seconds: Mapped[float | None] = mapped_column(Float)

    # Results
    metrics: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    # e.g. {"faithfulness": 0.91, "toxicity": 0.02, "latency_p99_ms": 3200}
    thresholds_breached: Mapped[list | None] = mapped_column(JSONB, default=list)
    alerts_fired: Mapped[list | None] = mapped_column(JSONB, default=list)

    drift_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    recertification_triggered: Mapped[bool] = mapped_column(Boolean, default=False)

    # Evidence
    artifact_ids: Mapped[list | None] = mapped_column(JSONB, default=list)

    total_canaries: Mapped[int] = mapped_column(Integer, default=0)
    canaries_passed: Mapped[int] = mapped_column(Integer, default=0)

    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Relationships
    plan: Mapped["MonitoringPlan"] = relationship(back_populates="executions")

    def __repr__(self) -> str:
        return f"<MonitoringExecution id={self.id} drift={self.drift_detected}>"


from app.models.genai_use_case import GenAIUseCase  # noqa: E402
