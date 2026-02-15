"""Vendor CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.vendor import Vendor
from app.schemas.common import PaginatedResponse
from app.schemas.vendor import VendorCreate, VendorListResponse, VendorResponse, VendorUpdate

router = APIRouter()


@router.get("", response_model=PaginatedResponse[VendorListResponse])
async def list_vendors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all vendors with pagination and search."""
    query = select(Vendor).where(Vendor.is_deleted == False)  # noqa: E712
    count_query = select(func.count()).select_from(Vendor).where(Vendor.is_deleted == False)  # noqa: E712

    if search:
        query = query.where(Vendor.name.ilike(f"%{search}%"))
        count_query = count_query.where(Vendor.name.ilike(f"%{search}%"))

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size).order_by(Vendor.created_at.desc()))
    vendors = result.scalars().all()

    return PaginatedResponse(
        items=[VendorListResponse.model_validate(v) for v in vendors],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=VendorResponse, status_code=201)
async def create_vendor(payload: VendorCreate, db: AsyncSession = Depends(get_db)):
    """Create a new vendor."""
    vendor = Vendor(**payload.model_dump())
    db.add(vendor)
    await db.flush()
    await db.refresh(vendor)
    return VendorResponse.model_validate(vendor)


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(vendor_id: str, db: AsyncSession = Depends(get_db)):
    """Get a vendor by ID."""
    vendor = await db.get(Vendor, vendor_id)
    if not vendor or vendor.is_deleted:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return VendorResponse.model_validate(vendor)


@router.patch("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: str, payload: VendorUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a vendor."""
    vendor = await db.get(Vendor, vendor_id)
    if not vendor or vendor.is_deleted:
        raise HTTPException(status_code=404, detail="Vendor not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(vendor, key, value)

    await db.flush()
    await db.refresh(vendor)
    return VendorResponse.model_validate(vendor)


@router.delete("/{vendor_id}", status_code=204)
async def delete_vendor(vendor_id: str, db: AsyncSession = Depends(get_db)):
    """Soft-delete a vendor."""
    vendor = await db.get(Vendor, vendor_id)
    if not vendor or vendor.is_deleted:
        raise HTTPException(status_code=404, detail="Vendor not found")

    vendor.is_deleted = True
    await db.flush()
