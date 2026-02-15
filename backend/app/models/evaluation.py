"""Evaluation entities – test runs, results, and harness metadata."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, AuditMixin, generate_uuid


class EvalType(str, enum.Enum):
    QUALITY_CORRECTNESS = "quality_correctness"
    SAFETY_SECURITY = "safety_security"
    OPERATIONAL_CONTROLS = "operational_controls"
    RAG_GROUNDEDNESS = "rag_groundedness"
    RED_TEAM_PROMPTFOO = "red_team_promptfoo"
    RED_TEAM_PYRIT = "red_team_pyrit"
    VULNERABILITY_GARAK = "vulnerability_garak"
    REGRESSION = "regression"
    CANARY = "canary"
    AGENTIC_SAFETY = "agentic_safety"


class EvalStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvaluationRun(Base, TimestampMixin, AuditMixin):
    """A single evaluation execution (test run)."""

    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    eval_type: Mapped[EvalType] = mapped_column(
        SAEnum(EvalType, name="eval_type"),
        nullable=False,
    )
    status: Mapped[EvalStatus] = mapped_column(
        SAEnum(EvalStatus, name="eval_status"),
        default=EvalStatus.PENDING,
    )

    # Linked entities
    use_case_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("genai_use_cases.id")
    )
    model_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("models.id")
    )
    dataset_id: Mapped[str | None] = mapped_column(String(36))

    # Execution details
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    worker_id: Mapped[str | None] = mapped_column(String(100))

    # Provider / version tracking (FINRA requirement)
    model_provider: Mapped[str | None] = mapped_column(String(100))
    model_version: Mapped[str | None] = mapped_column(String(100))
    prompt_template_hash: Mapped[str | None] = mapped_column(String(64))

    # Config used for this run
    eval_config: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Aggregate scores
    total_tests: Mapped[int] = mapped_column(Integer, default=0)
    passed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[int] = mapped_column(Integer, default=0)
    pass_rate: Mapped[float | None] = mapped_column(Float)
    aggregate_scores: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    # e.g. {"faithfulness": 0.92, "relevance": 0.88, "toxicity": 0.01}

    # OWASP mapping for security evals
    owasp_category_results: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    # e.g. {"LLM01_prompt_injection": {"tested": 50, "passed": 48, "failed": 2}}

    # Evidence artifacts
    artifact_ids: Mapped[list | None] = mapped_column(JSONB, default=list)

    # Relationships
    use_case: Mapped["GenAIUseCase | None"] = relationship(back_populates="evaluation_runs")
    model: Mapped["Model | None"] = relationship(back_populates="evaluation_runs")
    results: Mapped[list["EvaluationResult"]] = relationship(
        back_populates="run", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<EvaluationRun id={self.id} type={self.eval_type} status={self.status}>"


class EvaluationResult(Base, TimestampMixin):
    """Individual test case result within an evaluation run."""

    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evaluation_runs.id"), nullable=False
    )

    test_case_id: Mapped[str] = mapped_column(String(100), nullable=False)
    test_case_name: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(100))

    # Input / Output capture (with PII redaction)
    input_prompt: Mapped[str | None] = mapped_column(Text)
    expected_output: Mapped[str | None] = mapped_column(Text)
    actual_output: Mapped[str | None] = mapped_column(Text)
    context_used: Mapped[str | None] = mapped_column(Text)  # For RAG evals

    # Scoring
    passed: Mapped[bool | None] = mapped_column()
    score: Mapped[float | None] = mapped_column(Float)
    threshold: Mapped[float | None] = mapped_column(Float)
    metrics: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Latency & cost tracking
    latency_ms: Mapped[float | None] = mapped_column(Float)
    token_count_input: Mapped[int | None] = mapped_column(Integer)
    token_count_output: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[float | None] = mapped_column(Float)

    # Error details
    error_message: Mapped[str | None] = mapped_column(Text)

    # OWASP risk category (if security test)
    owasp_risk_id: Mapped[str | None] = mapped_column(String(50))
    # e.g. "LLM01", "ASI02"

    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Relationships
    run: Mapped["EvaluationRun"] = relationship(back_populates="results")

    def __repr__(self) -> str:
        return f"<EvaluationResult id={self.id} passed={self.passed}>"


from app.models.genai_use_case import GenAIUseCase  # noqa: E402
from app.models.model import Model  # noqa: E402
