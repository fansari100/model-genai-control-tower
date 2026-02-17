"""
SEC 17a-4 Recordkeeping Service
================================
Implements broker-dealer-grade retention, retrieval, and immutability
for all evidence artifacts and audit records.

Aligned with:
  - SEC Rule 17a-4(b)(1), (b)(4), (b)(7)
  - FINRA Rules 3110, 4511
  - NIST AI 600-1 Content Provenance
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum

from pydantic import BaseModel


class RetentionClass(StrEnum):
    """SEC 17a-4 retention classifications."""

    STANDARD = "standard"  # 3 years
    REGULATORY = "regulatory"  # 7 years (17a-4 default)
    PERMANENT = "permanent"  # indefinite


class StorageTier(StrEnum):
    """Storage tier based on age of record."""

    HOT = "hot"  # < 2 years — readily accessible (17a-4 requirement)
    WARM = "warm"  # 2-7 years — retrievable within 4 hours
    ARCHIVE = "archive"  # > 7 years — Glacier Deep Archive


RETENTION_YEARS = {
    RetentionClass.STANDARD: 3,
    RetentionClass.REGULATORY: 7,
    RetentionClass.PERMANENT: 100,  # effectively permanent
}

# SEC 17a-4(b) requires first 2 years in "readily accessible" location
READILY_ACCESSIBLE_YEARS = 2


class RetentionPolicy(BaseModel):
    """Retention policy for a specific artifact type."""

    artifact_type: str
    retention_class: RetentionClass
    retention_years: int
    sec_reference: str
    description: str


# ── Retention Schedule (maps to sec_17a4_retention_schedule.yaml) ──

RETENTION_SCHEDULE: list[RetentionPolicy] = [
    RetentionPolicy(
        artifact_type="prompt_output_log",
        retention_class=RetentionClass.REGULATORY,
        retention_years=7,
        sec_reference="17a-4(b)(1)",
        description="GenAI prompt/output logs with model version stamps",
    ),
    RetentionPolicy(
        artifact_type="approval_record",
        retention_class=RetentionClass.REGULATORY,
        retention_years=7,
        sec_reference="17a-4(b)(4)",
        description="Governance approval decisions with decision_hash",
    ),
    RetentionPolicy(
        artifact_type="certification_pack",
        retention_class=RetentionClass.REGULATORY,
        retention_years=7,
        sec_reference="17a-4(b)(7)",
        description="8-section certification evidence packs",
    ),
    RetentionPolicy(
        artifact_type="test_results",
        retention_class=RetentionClass.REGULATORY,
        retention_years=7,
        sec_reference="SR 11-7",
        description="Evaluation run results and red-team reports",
    ),
    RetentionPolicy(
        artifact_type="findings_register",
        retention_class=RetentionClass.REGULATORY,
        retention_years=7,
        sec_reference="SR 11-7",
        description="Findings with remediation history",
    ),
    RetentionPolicy(
        artifact_type="aibom",
        retention_class=RetentionClass.PERMANENT,
        retention_years=100,
        sec_reference="NIST AI 600-1",
        description="AI Bill of Materials for all governed models",
    ),
]


def get_retention_policy(artifact_type: str) -> RetentionPolicy | None:
    """Look up retention policy for an artifact type."""
    return next((p for p in RETENTION_SCHEDULE if p.artifact_type == artifact_type), None)


def compute_retention_until(artifact_type: str, created_at: datetime | None = None) -> datetime:
    """Compute the retention expiry date for an artifact."""
    policy = get_retention_policy(artifact_type)
    years = policy.retention_years if policy else 7  # Default to regulatory
    base = created_at or datetime.now(UTC)
    return base + timedelta(days=years * 365)


def get_storage_tier(created_at: datetime) -> StorageTier:
    """Determine storage tier based on artifact age (SEC 17a-4 first 2 years rule)."""
    age_years = (datetime.now(UTC) - created_at).days / 365
    if age_years < READILY_ACCESSIBLE_YEARS:
        return StorageTier.HOT
    if age_years < 7:
        return StorageTier.WARM
    return StorageTier.ARCHIVE


def get_retention_summary() -> dict:
    """Return a summary of all retention policies for compliance reporting."""
    return {
        "total_policies": len(RETENTION_SCHEDULE),
        "policies": [p.model_dump() for p in RETENTION_SCHEDULE],
        "readily_accessible_years": READILY_ACCESSIBLE_YEARS,
        "default_retention_years": 7,
        "immutability_mechanism": "S3 Object Lock (GOVERNANCE mode) + SHA-256 hash chains",
    }
