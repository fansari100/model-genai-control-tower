"""Dataset entity – golden test sets, eval corpora, retrieval sources."""

from __future__ import annotations

import enum

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin, generate_uuid


class DatasetType(enum.StrEnum):
    GOLDEN_TEST_SET = "golden_test_set"
    RETRIEVAL_CORPUS = "retrieval_corpus"
    TRAINING_DATA = "training_data"
    CALIBRATION = "calibration"
    CANARY = "canary"
    RED_TEAM = "red_team"


class Dataset(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), default="1.0")
    description: Mapped[str | None] = mapped_column(Text)

    dataset_type: Mapped[DatasetType] = mapped_column(
        SAEnum(DatasetType, name="dataset_type"),
        nullable=False,
    )

    # Data characteristics
    record_count: Mapped[int | None] = mapped_column(Integer)
    contains_pii: Mapped[bool] = mapped_column(Boolean, default=False)
    data_classification: Mapped[str | None] = mapped_column(String(50))
    source_description: Mapped[str | None] = mapped_column(Text)

    # Storage
    storage_location: Mapped[str | None] = mapped_column(String(500))
    artifact_hash: Mapped[str | None] = mapped_column(String(64))  # SHA-256

    # Provenance (NIST content provenance)
    provenance: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    # e.g. {"source": "internal_knowledge_base", "extraction_date": "...", "curator": "..."}

    # Schema / format
    schema_definition: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    format: Mapped[str | None] = mapped_column(String(50))  # jsonl, csv, parquet, etc.

    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    def __repr__(self) -> str:
        return f"<Dataset id={self.id} name={self.name} type={self.dataset_type}>"
