"""Finding CRUD endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from app.database import get_db
from app.models.finding import Finding, FindingSeverity, FindingSource, FindingStatus
from app.schemas.common import PaginatedResponse
from app.schemas.finding import FindingCreate, FindingResponse, FindingUpdate

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", response_model=PaginatedResponse[FindingResponse])
async def list_findings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: FindingSeverity | None = None,
    status: FindingStatus | None = None,
    source: FindingSource | None = None,
    use_case_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Finding)
    count_query = select(func.count()).select_from(Finding)

    if severity:
        query = query.where(Finding.severity == severity)
        count_query = count_query.where(Finding.severity == severity)
    if status:
        query = query.where(Finding.status == status)
        count_query = count_query.where(Finding.status == status)
    if source:
        query = query.where(Finding.source == source)
        count_query = count_query.where(Finding.source == source)
    if use_case_id:
        query = query.where(Finding.use_case_id == use_case_id)
        count_query = count_query.where(Finding.use_case_id == use_case_id)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.offset(offset).limit(page_size).order_by(Finding.created_at.desc())
    )
    findings = result.scalars().all()

    return PaginatedResponse(
        items=[FindingResponse.model_validate(f) for f in findings],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=FindingResponse, status_code=201)
async def create_finding(payload: FindingCreate, db: AsyncSession = Depends(get_db)):
    finding = Finding(**payload.model_dump())
    db.add(finding)
    await db.flush()
    await db.refresh(finding)
    return FindingResponse.model_validate(finding)


@router.get("/{finding_id}", response_model=FindingResponse)
async def get_finding(finding_id: str, db: AsyncSession = Depends(get_db)):
    finding = await db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return FindingResponse.model_validate(finding)


@router.patch("/{finding_id}", response_model=FindingResponse)
async def update_finding(
    finding_id: str, payload: FindingUpdate, db: AsyncSession = Depends(get_db)
):
    finding = await db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(finding, key, value)

    await db.flush()
    await db.refresh(finding)
    return FindingResponse.model_validate(finding)
