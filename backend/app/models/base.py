"""Shared base mixin for all domain models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    """created_at / updated_at columns for every table."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        server_default=text("now()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        server_default=text("now()"),
        nullable=False,
    )


class SoftDeleteMixin:
    """Soft-delete support."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
    )
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)


class AuditMixin:
    """Who created / last modified."""

    created_by: Mapped[str] = mapped_column(String(255), default="system", nullable=False)
    updated_by: Mapped[str] = mapped_column(String(255), default="system", nullable=False)
