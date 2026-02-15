"""Tool / EUC CRUD + attestation endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select

from app.database import get_db
from app.models.tool import Tool, ToolCategory, ToolCriticality, ToolStatus
from app.schemas.common import PaginatedResponse
from app.schemas.tool import ToolCreate, ToolListResponse, ToolResponse, ToolUpdate

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ToolListResponse])
async def list_tools(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    category: ToolCategory | None = None,
    criticality: ToolCriticality | None = None,
    status: ToolStatus | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all registered tools / EUCs."""
    query = select(Tool).where(Tool.is_deleted == False)  # noqa: E712
    count_query = select(func.count()).select_from(Tool).where(Tool.is_deleted == False)  # noqa: E712

    if search:
        query = query.where(Tool.name.ilike(f"%{search}%"))
        count_query = count_query.where(Tool.name.ilike(f"%{search}%"))
    if category:
        query = query.where(Tool.category == category)
        count_query = count_query.where(Tool.category == category)
    if criticality:
        query = query.where(Tool.criticality == criticality)
        count_query = count_query.where(Tool.criticality == criticality)
    if status:
        query = query.where(Tool.status == status)
        count_query = count_query.where(Tool.status == status)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.offset(offset).limit(page_size).order_by(Tool.created_at.desc())
    )
    tools = result.scalars().all()

    return PaginatedResponse(
        items=[ToolListResponse.model_validate(t) for t in tools],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=ToolResponse, status_code=201)
async def create_tool(payload: ToolCreate, db: AsyncSession = Depends(get_db)):
    """Register a new tool / EUC in the inventory."""
    tool = Tool(**payload.model_dump())
    db.add(tool)
    await db.flush()
    await db.refresh(tool)
    return ToolResponse.model_validate(tool)


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(tool_id: str, db: AsyncSession = Depends(get_db)):
    tool = await db.get(Tool, tool_id)
    if not tool or tool.is_deleted:
        raise HTTPException(status_code=404, detail="Tool not found")
    return ToolResponse.model_validate(tool)


@router.patch("/{tool_id}", response_model=ToolResponse)
async def update_tool(tool_id: str, payload: ToolUpdate, db: AsyncSession = Depends(get_db)):
    tool = await db.get(Tool, tool_id)
    if not tool or tool.is_deleted:
        raise HTTPException(status_code=404, detail="Tool not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tool, key, value)

    await db.flush()
    await db.refresh(tool)
    return ToolResponse.model_validate(tool)


@router.delete("/{tool_id}", status_code=204)
async def delete_tool(tool_id: str, db: AsyncSession = Depends(get_db)):
    tool = await db.get(Tool, tool_id)
    if not tool or tool.is_deleted:
        raise HTTPException(status_code=404, detail="Tool not found")
    tool.is_deleted = True
    await db.flush()


@router.post("/{tool_id}/attest", response_model=ToolResponse)
async def attest_tool(tool_id: str, db: AsyncSession = Depends(get_db)):
    """
    Complete an attestation for a tool / EUC.
    Updates attestation dates and transitions status.
    """
    tool = await db.get(Tool, tool_id)
    if not tool or tool.is_deleted:
        raise HTTPException(status_code=404, detail="Tool not found")

    now = datetime.now(UTC)
    tool.last_attestation_date = now
    tool.status = ToolStatus.ATTESTED
    if tool.attestation_frequency_days:
        tool.next_attestation_date = now + timedelta(days=tool.attestation_frequency_days)

    await db.flush()
    await db.refresh(tool)
    return ToolResponse.model_validate(tool)
