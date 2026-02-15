"""Model CRUD + governance endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.model import Model, ModelStatus, ModelType, RiskTier
from app.schemas.common import PaginatedResponse
from app.schemas.model import ModelCreate, ModelListResponse, ModelResponse, ModelUpdate

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ModelListResponse])
async def list_models(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    model_type: ModelType | None = None,
    status: ModelStatus | None = None,
    risk_tier: RiskTier | None = None,
    vendor_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List models with filtering, pagination, and search."""
    query = select(Model).where(Model.is_deleted == False)  # noqa: E712
    count_query = select(func.count()).select_from(Model).where(Model.is_deleted == False)  # noqa: E712

    if search:
        query = query.where(Model.name.ilike(f"%{search}%"))
        count_query = count_query.where(Model.name.ilike(f"%{search}%"))
    if model_type:
        query = query.where(Model.model_type == model_type)
        count_query = count_query.where(Model.model_type == model_type)
    if status:
        query = query.where(Model.status == status)
        count_query = count_query.where(Model.status == status)
    if risk_tier:
        query = query.where(Model.risk_tier == risk_tier)
        count_query = count_query.where(Model.risk_tier == risk_tier)
    if vendor_id:
        query = query.where(Model.vendor_id == vendor_id)
        count_query = count_query.where(Model.vendor_id == vendor_id)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.offset(offset).limit(page_size).order_by(Model.created_at.desc())
    )
    models = result.scalars().all()

    return PaginatedResponse(
        items=[ModelListResponse.model_validate(m) for m in models],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=ModelResponse, status_code=201)
async def create_model(payload: ModelCreate, db: AsyncSession = Depends(get_db)):
    """Register a new model in the inventory."""
    model = Model(**payload.model_dump())
    db.add(model)
    await db.flush()
    await db.refresh(model)
    return ModelResponse.model_validate(model)


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: str, db: AsyncSession = Depends(get_db)):
    """Get model details."""
    model = await db.get(Model, model_id)
    if not model or model.is_deleted:
        raise HTTPException(status_code=404, detail="Model not found")
    return ModelResponse.model_validate(model)


@router.patch("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: str, payload: ModelUpdate, db: AsyncSession = Depends(get_db)
):
    """Update model details."""
    model = await db.get(Model, model_id)
    if not model or model.is_deleted:
        raise HTTPException(status_code=404, detail="Model not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(model, key, value)

    await db.flush()
    await db.refresh(model)
    return ModelResponse.model_validate(model)


@router.delete("/{model_id}", status_code=204)
async def delete_model(model_id: str, db: AsyncSession = Depends(get_db)):
    """Soft-delete a model."""
    model = await db.get(Model, model_id)
    if not model or model.is_deleted:
        raise HTTPException(status_code=404, detail="Model not found")
    model.is_deleted = True
    await db.flush()


@router.post("/{model_id}/transition", response_model=ModelResponse)
async def transition_model_status(
    model_id: str,
    new_status: ModelStatus,
    db: AsyncSession = Depends(get_db),
):
    """Transition model governance status (with validation)."""
    model = await db.get(Model, model_id)
    if not model or model.is_deleted:
        raise HTTPException(status_code=404, detail="Model not found")

    # Status transition validation
    valid_transitions: dict[ModelStatus, list[ModelStatus]] = {
        ModelStatus.DRAFT: [ModelStatus.INTAKE],
        ModelStatus.INTAKE: [ModelStatus.UNDER_REVIEW, ModelStatus.DRAFT],
        ModelStatus.UNDER_REVIEW: [ModelStatus.APPROVED, ModelStatus.CONDITIONAL, ModelStatus.DRAFT],
        ModelStatus.APPROVED: [ModelStatus.DEPRECATED, ModelStatus.UNDER_REVIEW],
        ModelStatus.CONDITIONAL: [ModelStatus.APPROVED, ModelStatus.DEPRECATED, ModelStatus.UNDER_REVIEW],
        ModelStatus.DEPRECATED: [ModelStatus.RETIRED, ModelStatus.UNDER_REVIEW],
        ModelStatus.RETIRED: [],
    }

    if new_status not in valid_transitions.get(model.status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from {model.status} to {new_status}",
        )

    model.status = new_status
    await db.flush()
    await db.refresh(model)
    return ModelResponse.model_validate(model)
