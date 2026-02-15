"""Evaluation run endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from app.auth import CurrentUser, require_write
from app.database import get_db
from app.models.evaluation import EvalStatus, EvalType, EvaluationResult, EvaluationRun
from app.schemas.common import PaginatedResponse
from app.schemas.evaluation import (
    EvalResultResponse,
    EvalRunCreate,
    EvalRunListResponse,
    EvalRunResponse,
    TriggerEvalRequest,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", response_model=PaginatedResponse[EvalRunListResponse])
async def list_evaluations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    eval_type: EvalType | None = None,
    status: EvalStatus | None = None,
    use_case_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List evaluation runs."""
    query = select(EvaluationRun)
    count_query = select(func.count()).select_from(EvaluationRun)

    if eval_type:
        query = query.where(EvaluationRun.eval_type == eval_type)
        count_query = count_query.where(EvaluationRun.eval_type == eval_type)
    if status:
        query = query.where(EvaluationRun.status == status)
        count_query = count_query.where(EvaluationRun.status == status)
    if use_case_id:
        query = query.where(EvaluationRun.use_case_id == use_case_id)
        count_query = count_query.where(EvaluationRun.use_case_id == use_case_id)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.offset(offset).limit(page_size).order_by(EvaluationRun.created_at.desc())
    )
    runs = result.scalars().all()

    return PaginatedResponse(
        items=[EvalRunListResponse.model_validate(r) for r in runs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=EvalRunResponse, status_code=201)
async def create_evaluation(payload: EvalRunCreate, db: AsyncSession = Depends(get_db)):
    """Create and start an evaluation run."""
    run = EvaluationRun(
        **payload.model_dump(),
        status=EvalStatus.PENDING,
        started_at=datetime.now(UTC),
    )
    db.add(run)
    await db.flush()
    await db.refresh(run)
    return EvalRunResponse.model_validate(run)


@router.get("/{run_id}", response_model=EvalRunResponse)
async def get_evaluation(run_id: str, db: AsyncSession = Depends(get_db)):
    run = await db.get(EvaluationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    return EvalRunResponse.model_validate(run)


@router.get("/{run_id}/results", response_model=list[EvalResultResponse])
async def get_evaluation_results(run_id: str, db: AsyncSession = Depends(get_db)):
    """Get individual test results for an evaluation run."""
    result = await db.execute(
        select(EvaluationResult)
        .where(EvaluationResult.run_id == run_id)
        .order_by(EvaluationResult.created_at)
    )
    results = result.scalars().all()
    return [EvalResultResponse.model_validate(r) for r in results]


@router.post("/trigger", response_model=EvalRunResponse, status_code=201)
async def trigger_evaluation(
    payload: TriggerEvalRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_write),
):
    """
    Trigger a new evaluation run.
    Creates the run record and dispatches to Temporal if connected.
    """
    from app.config import get_settings

    settings = get_settings()

    run = EvaluationRun(
        name=f"{payload.eval_type.value}_run_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
        eval_type=payload.eval_type,
        use_case_id=payload.use_case_id,
        model_id=payload.model_id,
        dataset_id=payload.dataset_id,
        eval_config=payload.config_overrides or {},
        status=EvalStatus.PENDING,
        started_at=datetime.now(UTC),
        created_by=user.username,
        updated_by=user.username,
    )
    db.add(run)
    await db.flush()
    await db.refresh(run)

    # Dispatch to Temporal workflow if enabled
    if settings.enable_temporal:
        try:
            from temporalio.client import Client

            client = await Client.connect(
                settings.temporal_host, namespace=settings.temporal_namespace
            )
            await client.start_workflow(
                "certification-workflow",
                arg={
                    "use_case_id": payload.use_case_id or "",
                    "risk_rating": "medium",
                    "required_test_suites": [payload.eval_type.value],
                    "required_approvals": [],
                    "owner": user.username,
                    "initiated_by": user.username,
                },
                id=f"eval-{run.id}",
                task_queue=settings.temporal_task_queue,
            )
            run.status = EvalStatus.RUNNING
            await db.flush()
            await db.refresh(run)
        except Exception as e:
            import structlog

            structlog.get_logger().warning("temporal_dispatch_failed", error=str(e), run_id=run.id)

    return EvalRunResponse.model_validate(run)
