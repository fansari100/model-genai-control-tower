"""Evaluation schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.evaluation import EvalStatus, EvalType


class EvalRunCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    eval_type: EvalType
    use_case_id: str | None = None
    model_id: str | None = None
    dataset_id: str | None = None
    eval_config: dict | None = None


class EvalRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    eval_type: EvalType
    status: EvalStatus
    use_case_id: str | None = None
    model_id: str | None = None
    dataset_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    model_provider: str | None = None
    model_version: str | None = None
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    pass_rate: float | None = None
    aggregate_scores: dict | None = None
    owasp_category_results: dict | None = None
    artifact_ids: list | None = None
    created_at: datetime | None = None


class EvalResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    test_case_id: str
    test_case_name: str | None = None
    category: str | None = None
    input_prompt: str | None = None
    expected_output: str | None = None
    actual_output: str | None = None
    passed: bool | None = None
    score: float | None = None
    threshold: float | None = None
    metrics: dict | None = None
    latency_ms: float | None = None
    token_count_input: int | None = None
    token_count_output: int | None = None
    cost_usd: float | None = None
    owasp_risk_id: str | None = None
    created_at: datetime | None = None


class EvalRunListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    eval_type: EvalType
    status: EvalStatus
    use_case_id: str | None = None
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    pass_rate: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None


class TriggerEvalRequest(BaseModel):
    """Trigger a new evaluation run via the evaluation orchestrator."""

    eval_type: EvalType
    use_case_id: str | None = None
    model_id: str | None = None
    dataset_id: str | None = None
    config_overrides: dict | None = None
