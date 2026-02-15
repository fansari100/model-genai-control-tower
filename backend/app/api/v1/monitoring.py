"""Monitoring plan + execution endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.auth import CurrentUser, get_current_user
from app.database import get_db
from app.models.monitoring import (
    MonitoringCadence,
    MonitoringExecution,
    MonitoringPlan,
    MonitoringStatus,
)
from app.schemas.common import PaginatedResponse
from app.services.audit_events import AuditEvent, AuditEventType, audit_publisher
from app.workers.monitoring_worker import MonitoringWorker

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
_monitoring_worker = MonitoringWorker()


class MonitoringPlanCreate(BaseModel):
    name: str
    description: str | None = None
    use_case_id: str
    cadence: MonitoringCadence = MonitoringCadence.DAILY
    canary_prompts: list | None = None
    regression_dataset_id: str | None = None
    thresholds: dict | None = None
    alert_routing: dict | None = None
    recert_triggers: dict | None = None


class MonitoringPlanResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    description: str | None = None
    use_case_id: str
    status: MonitoringStatus
    cadence: MonitoringCadence
    canary_prompts: list | None = None
    thresholds: dict | None = None
    alert_routing: dict | None = None
    recert_triggers: dict | None = None
    created_at: datetime | None = None


class MonitoringExecResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    plan_id: str
    executed_at: datetime
    duration_seconds: float | None = None
    metrics: dict | None = None
    thresholds_breached: list | None = None
    alerts_fired: list | None = None
    drift_detected: bool
    recertification_triggered: bool
    total_canaries: int
    canaries_passed: int
    created_at: datetime | None = None


@router.get("/plans", response_model=PaginatedResponse[MonitoringPlanResponse])
async def list_monitoring_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_case_id: str | None = None,
    status: MonitoringStatus | None = None,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    query = select(MonitoringPlan)
    count_query = select(func.count()).select_from(MonitoringPlan)

    if use_case_id:
        query = query.where(MonitoringPlan.use_case_id == use_case_id)
        count_query = count_query.where(MonitoringPlan.use_case_id == use_case_id)
    if status:
        query = query.where(MonitoringPlan.status == status)
        count_query = count_query.where(MonitoringPlan.status == status)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.offset(offset).limit(page_size).order_by(MonitoringPlan.created_at.desc())
    )
    plans = result.scalars().all()

    return PaginatedResponse(
        items=[MonitoringPlanResponse.model_validate(p) for p in plans],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("/plans", response_model=MonitoringPlanResponse, status_code=201)
async def create_monitoring_plan(
    payload: MonitoringPlanCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    plan = MonitoringPlan(
        **payload.model_dump(), created_by=user.username, updated_by=user.username
    )
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return MonitoringPlanResponse.model_validate(plan)


@router.get("/plans/{plan_id}", response_model=MonitoringPlanResponse)
async def get_monitoring_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    plan = await db.get(MonitoringPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Monitoring plan not found")
    return MonitoringPlanResponse.model_validate(plan)


@router.get("/plans/{plan_id}/executions", response_model=list[MonitoringExecResponse])
async def list_plan_executions(
    plan_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(MonitoringExecution)
        .where(MonitoringExecution.plan_id == plan_id)
        .order_by(MonitoringExecution.executed_at.desc())
        .limit(limit)
    )
    executions = result.scalars().all()
    return [MonitoringExecResponse.model_validate(e) for e in executions]


@router.post("/plans/{plan_id}/execute", response_model=MonitoringExecResponse, status_code=201)
async def trigger_monitoring_execution(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Trigger a monitoring execution.
    Runs canary prompts, evaluates thresholds, detects drift,
    and triggers recertification if needed.
    """
    plan = await db.get(MonitoringPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Monitoring plan not found")

    # Execute monitoring via the worker
    worker_result = await _monitoring_worker.execute_monitoring_plan(
        plan_id=plan_id,
        canary_prompts=plan.canary_prompts or [],
        thresholds=plan.thresholds or {},
        recert_triggers=plan.recert_triggers or {},
    )

    # Persist execution result
    execution = MonitoringExecution(
        plan_id=plan_id,
        executed_at=datetime.now(UTC),
        duration_seconds=worker_result.get("duration_seconds"),
        metrics=worker_result.get("metrics", {}),
        thresholds_breached=worker_result.get("thresholds_breached", []),
        alerts_fired=worker_result.get("alerts_fired", []),
        drift_detected=worker_result.get("drift_detected", False),
        recertification_triggered=worker_result.get("recertification_triggered", False),
        total_canaries=worker_result.get("total_canaries", 0),
        canaries_passed=worker_result.get("canaries_passed", 0),
    )
    db.add(execution)
    await db.flush()
    await db.refresh(execution)

    # Emit audit events for drift/recert
    if execution.drift_detected:
        await audit_publisher.publish(
            AuditEvent(
                event_type=AuditEventType.MONITORING_DRIFT_DETECTED,
                entity_type="monitoring_plan",
                entity_id=plan_id,
                actor=user.username,
                data={"thresholds_breached": execution.thresholds_breached},
            )
        )
    if execution.recertification_triggered:
        await audit_publisher.publish(
            AuditEvent(
                event_type=AuditEventType.MONITORING_RECERT_TRIGGERED,
                entity_type="monitoring_plan",
                entity_id=plan_id,
                actor=user.username,
                data={"trigger_reason": "drift_detected"},
            )
        )

    return MonitoringExecResponse.model_validate(execution)
