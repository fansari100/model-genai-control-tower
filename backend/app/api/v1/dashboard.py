"""Dashboard / analytics endpoints – aggregated views for committee reporting."""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.database import get_db
from app.models.evaluation import EvalStatus, EvaluationRun
from app.models.finding import Finding
from app.models.genai_use_case import GenAIUseCase
from app.models.model import Model
from app.models.tool import Tool
from app.services.compliance_mapping import get_full_compliance_matrix

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/summary")
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """
    High-level summary for the Control Tower dashboard.
    Provides counts, status breakdowns, and risk distribution.
    """
    # Models
    model_total = (
        await db.execute(
            select(func.count()).select_from(Model).where(Model.is_deleted == False)  # noqa: E712
        )
    ).scalar_one()
    model_by_status = dict(
        (
            await db.execute(
                select(Model.status, func.count())
                .where(Model.is_deleted == False)  # noqa: E712
                .group_by(Model.status)
            )
        ).all()
    )

    # Tools / EUCs
    tool_total = (
        await db.execute(
            select(func.count()).select_from(Tool).where(Tool.is_deleted == False)  # noqa: E712
        )
    ).scalar_one()
    tool_by_status = dict(
        (
            await db.execute(
                select(Tool.status, func.count())
                .where(Tool.is_deleted == False)  # noqa: E712
                .group_by(Tool.status)
            )
        ).all()
    )

    # GenAI Use Cases
    uc_total = (
        await db.execute(
            select(func.count()).select_from(GenAIUseCase).where(GenAIUseCase.is_deleted == False)  # noqa: E712
        )
    ).scalar_one()
    uc_by_status = dict(
        (
            await db.execute(
                select(GenAIUseCase.status, func.count())
                .where(GenAIUseCase.is_deleted == False)  # noqa: E712
                .group_by(GenAIUseCase.status)
            )
        ).all()
    )
    uc_by_risk = dict(
        (
            await db.execute(
                select(GenAIUseCase.risk_rating, func.count())
                .where(GenAIUseCase.is_deleted == False)  # noqa: E712
                .group_by(GenAIUseCase.risk_rating)
            )
        ).all()
    )

    # Findings
    findings_total = (await db.execute(select(func.count()).select_from(Finding))).scalar_one()
    findings_open_critical = (
        await db.execute(
            select(func.count())
            .select_from(Finding)
            .where(sa.cast(Finding.status, sa.String).in_(["open", "in_progress"]))
            .where(sa.cast(Finding.severity, sa.String).in_(["critical", "high"]))
        )
    ).scalar_one()

    # Evaluations
    eval_total = (await db.execute(select(func.count()).select_from(EvaluationRun))).scalar_one()
    eval_recent_pass_rate = (
        await db.execute(
            select(func.avg(EvaluationRun.pass_rate)).where(
                EvaluationRun.status == EvalStatus.COMPLETED
            )
        )
    ).scalar_one()

    return {
        "inventory": {
            "models": {
                "total": model_total,
                "by_status": {str(k): v for k, v in model_by_status.items()},
            },
            "tools": {
                "total": tool_total,
                "by_status": {str(k): v for k, v in tool_by_status.items()},
            },
            "use_cases": {
                "total": uc_total,
                "by_status": {str(k): v for k, v in uc_by_status.items()},
                "by_risk": {str(k): v for k, v in uc_by_risk.items()},
            },
        },
        "risk_posture": {
            "open_critical_findings": findings_open_critical,
            "total_findings": findings_total,
            "avg_eval_pass_rate": round(eval_recent_pass_rate, 2)
            if eval_recent_pass_rate
            else None,
            "total_evaluations": eval_total,
        },
        "compliance": {
            "frameworks": [
                "SR 11-7",
                "NIST AI 600-1",
                "OWASP LLM Top 10 2025",
                "OWASP Agentic Top 10 2026",
                "ISO/IEC 42001",
                "MITRE ATLAS",
            ],
            "status": "active",
        },
    }


@router.get("/committee-report")
async def get_committee_report(db: AsyncSession = Depends(get_db)):
    """
    Generate data for committee reporting dashboard.
    Provides the aggregated view that VPs care about.
    """
    # Use case pipeline funnel
    pipeline = dict(
        (
            await db.execute(
                select(GenAIUseCase.status, func.count())
                .where(GenAIUseCase.is_deleted == False)  # noqa: E712
                .group_by(GenAIUseCase.status)
            )
        ).all()
    )

    # Tools requiring attestation
    tools_needing_attestation = (
        await db.execute(
            select(func.count())
            .select_from(Tool)
            .where(Tool.is_deleted == False)  # noqa: E712
            .where(sa.cast(Tool.status, sa.String).in_(["attestation_due", "attestation_overdue"]))
        )
    ).scalar_one()

    # Findings aging
    findings_by_severity = dict(
        (
            await db.execute(
                select(Finding.severity, func.count())
                .where(sa.cast(Finding.status, sa.String).in_(["open", "in_progress"]))
                .group_by(Finding.severity)
            )
        ).all()
    )

    return {
        "report_title": "Control Tower – Committee Report",
        "generated_by": "Control Tower v1.0",
        "use_case_pipeline": {str(k): v for k, v in pipeline.items()},
        "tools_needing_attestation": tools_needing_attestation,
        "open_findings_by_severity": {str(k): v for k, v in findings_by_severity.items()},
        "key_metrics": {
            "total_governed_assets": 0,  # Computed in production
            "certification_completion_rate": 0.0,
            "average_time_to_certify_days": 0,
        },
    }


@router.get("/compliance-matrix")
async def get_compliance_matrix():
    """
    Return the full compliance control mapping.
    Maps every OWASP, NIST, SR 11-7, FINRA, and MITRE ATLAS requirement
    to the specific Control Tower control that addresses it.
    """
    return get_full_compliance_matrix()
