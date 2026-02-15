"""Shared schema components."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    environment: str


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class AuditInfo(BaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None
    trace_id: str | None = None


class BulkActionRequest(BaseModel):
    ids: list[str]
    action: str


class BulkActionResponse(BaseModel):
    succeeded: list[str]
    failed: list[dict]
    total_processed: int
