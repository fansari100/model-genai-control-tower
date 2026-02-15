"""Approval gate endpoints."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from app.auth import CurrentUser, require_approver
from app.database import get_db
from app.models.approval import Approval, ApprovalDecision, ApprovalGateType
from app.schemas.approval import ApprovalCreate, ApprovalResponse
from app.schemas.common import PaginatedResponse
from app.services.audit_events import emit_approval

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ApprovalResponse])
async def list_approvals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    gate_type: ApprovalGateType | None = None,
    decision: ApprovalDecision | None = None,
    use_case_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Approval)
    count_query = select(func.count()).select_from(Approval)

    if gate_type:
        query = query.where(Approval.gate_type == gate_type)
        count_query = count_query.where(Approval.gate_type == gate_type)
    if decision:
        query = query.where(Approval.decision == decision)
        count_query = count_query.where(Approval.decision == decision)
    if use_case_id:
        query = query.where(Approval.use_case_id == use_case_id)
        count_query = count_query.where(Approval.use_case_id == use_case_id)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.offset(offset).limit(page_size).order_by(Approval.created_at.desc())
    )
    approvals = result.scalars().all()

    return PaginatedResponse(
        items=[ApprovalResponse.model_validate(a) for a in approvals],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=ApprovalResponse, status_code=201)
async def create_approval(
    payload: ApprovalCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_approver),
):
    """
    Record an approval decision with tamper-evident hash.
    Requires approver role (model_risk_officer, business_line_head, or admin).
    """
    approval = Approval(**payload.model_dump(), created_by=user.username, updated_by=user.username)

    # Generate tamper-evident hash of the decision record
    decision_record = {
        "gate_type": payload.gate_type.value,
        "decision": payload.decision.value,
        "approver_role": payload.approver_role,
        "approver_name": payload.approver_name,
        "rationale": payload.rationale,
        "conditions": payload.conditions,
        "use_case_id": payload.use_case_id,
    }
    approval.decision_hash = hashlib.sha256(
        json.dumps(decision_record, sort_keys=True, default=str).encode()
    ).hexdigest()

    db.add(approval)
    await db.flush()
    await db.refresh(approval)

    # Emit audit event
    await emit_approval(
        approval_id=approval.id,
        decision=payload.decision.value,
        gate_type=payload.gate_type.value,
        use_case_id=payload.use_case_id or "",
        approver=user.username,
    )

    return ApprovalResponse.model_validate(approval)


@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(approval_id: str, db: AsyncSession = Depends(get_db)):
    approval = await db.get(Approval, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return ApprovalResponse.model_validate(approval)
