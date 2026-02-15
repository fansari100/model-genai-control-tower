"""Certification pack generation endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select

from app.database import get_db
from app.models.approval import Approval
from app.models.evaluation import EvaluationRun
from app.models.finding import Finding
from app.models.genai_use_case import GenAIUseCase
from app.models.monitoring import MonitoringPlan
from app.schemas.evidence import CertificationPackRequest, CertificationPackResponse
from app.utils.pdf_generator import generate_certification_pack_pdf

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/generate", response_model=CertificationPackResponse)
async def generate_certification_pack(
    payload: CertificationPackRequest, db: AsyncSession = Depends(get_db)
):
    """
    Generate a complete certification evidence pack for a use case.
    Produces audit-grade documentation including test plans, results,
    findings, approvals, monitoring plans, and trace evidence.
    """
    use_case = await db.get(GenAIUseCase, payload.use_case_id)
    if not use_case:
        raise HTTPException(status_code=404, detail="Use case not found")

    sections: list[dict] = []
    artifact_ids: list[str] = []

    # Section 1: Use Case Summary & Risk Assessment
    sections.append(
        {
            "section": "1_use_case_summary",
            "title": "Use Case Summary & Risk Assessment",
            "content": {
                "name": use_case.name,
                "description": use_case.description,
                "category": use_case.category.value if use_case.category else None,
                "risk_rating": use_case.risk_rating.value if use_case.risk_rating else None,
                "data_classification": use_case.data_classification.value
                if use_case.data_classification
                else None,
                "client_facing": use_case.client_facing,
                "uses_agents": use_case.uses_agents,
                "uses_rag": use_case.uses_rag,
                "owner": use_case.owner,
                "business_unit": use_case.business_unit,
            },
        }
    )

    # Section 2: NIST GenAI Profile Mapping
    sections.append(
        {
            "section": "2_nist_genai_profile",
            "title": "NIST AI 600-1 GenAI Profile Compliance",
            "content": {
                "governance_controls": use_case.nist_governance_controls,
                "content_provenance": use_case.nist_content_provenance,
                "predeployment_testing": use_case.nist_predeployment_testing,
                "incident_disclosure": use_case.nist_incident_disclosure,
            },
        }
    )

    # Section 3: OWASP Risk Mapping
    sections.append(
        {
            "section": "3_owasp_risk_mapping",
            "title": "OWASP LLM Top 10 (2025) & Agentic Top 10 (2026) Mapping",
            "content": {
                "llm_top10": use_case.owasp_llm_top10_risks,
                "agentic_top10": use_case.owasp_agentic_top10_risks,
            },
        }
    )

    # Section 4: Test Results
    if payload.include_test_results:
        result = await db.execute(
            select(EvaluationRun)
            .where(EvaluationRun.use_case_id == payload.use_case_id)
            .order_by(EvaluationRun.created_at.desc())
        )
        eval_runs = result.scalars().all()
        sections.append(
            {
                "section": "4_test_results",
                "title": "Pre-Deployment Testing Results",
                "content": {
                    "total_runs": len(eval_runs),
                    "runs": [
                        {
                            "id": r.id,
                            "name": r.name,
                            "type": r.eval_type.value if r.eval_type else None,
                            "status": r.status.value if r.status else None,
                            "total_tests": r.total_tests,
                            "passed": r.passed,
                            "failed": r.failed,
                            "pass_rate": r.pass_rate,
                            "aggregate_scores": r.aggregate_scores,
                            "owasp_results": r.owasp_category_results,
                            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                        }
                        for r in eval_runs
                    ],
                },
            }
        )

    # Section 5: Findings Register
    if payload.include_findings:
        result = await db.execute(
            select(Finding)
            .where(Finding.use_case_id == payload.use_case_id)
            .order_by(Finding.severity)
        )
        findings = result.scalars().all()
        sections.append(
            {
                "section": "5_findings_register",
                "title": "Findings Register",
                "content": {
                    "total_findings": len(findings),
                    "by_severity": {},
                    "findings": [
                        {
                            "id": f.id,
                            "title": f.title,
                            "severity": f.severity.value,
                            "status": f.status.value,
                            "source": f.source.value,
                            "owasp_risk_id": f.owasp_risk_id,
                            "remediation_owner": f.remediation_owner,
                            "remediation_due_date": f.remediation_due_date.isoformat()
                            if f.remediation_due_date
                            else None,
                        }
                        for f in findings
                    ],
                },
            }
        )

    # Section 6: Approval Record
    if payload.include_approvals:
        result = await db.execute(
            select(Approval)
            .where(Approval.use_case_id == payload.use_case_id)
            .order_by(Approval.created_at.desc())
        )
        approvals = result.scalars().all()
        sections.append(
            {
                "section": "6_approval_record",
                "title": "Governance Approval Record",
                "content": {
                    "total_approvals": len(approvals),
                    "approvals": [
                        {
                            "id": a.id,
                            "gate_type": a.gate_type.value,
                            "decision": a.decision.value,
                            "approver_role": a.approver_role,
                            "approver_name": a.approver_name,
                            "rationale": a.rationale,
                            "conditions": a.conditions,
                            "decision_hash": a.decision_hash,
                            "timestamp": a.created_at.isoformat() if a.created_at else None,
                        }
                        for a in approvals
                    ],
                },
            }
        )

    # Section 7: Monitoring Plan
    if payload.include_monitoring_plan:
        result = await db.execute(
            select(MonitoringPlan).where(MonitoringPlan.use_case_id == payload.use_case_id)
        )
        plans = result.scalars().all()
        sections.append(
            {
                "section": "7_monitoring_plan",
                "title": "Ongoing Monitoring Plan",
                "content": {
                    "plans": [
                        {
                            "id": p.id,
                            "name": p.name,
                            "cadence": p.cadence.value if p.cadence else None,
                            "thresholds": p.thresholds,
                            "alert_routing": p.alert_routing,
                            "recert_triggers": p.recert_triggers,
                        }
                        for p in plans
                    ],
                },
            }
        )

    # Section 8: ISO 42001 PDCA Mapping
    sections.append(
        {
            "section": "8_iso42001_pdca",
            "title": "ISO/IEC 42001 AIMS Lifecycle Mapping",
            "content": {
                "current_phase": use_case.iso42001_phase,
                "plan": "Use case intake + risk assessment completed",
                "do": "Implementation + testing",
                "check": "Monitoring + audits active",
                "act": "Remediation + continuous improvement",
            },
        }
    )

    # Determine overall status
    open_critical = 0
    if payload.include_findings:
        result2 = await db.execute(
            select(Finding)
            .where(Finding.use_case_id == payload.use_case_id)
            .where(Finding.severity.in_(["critical", "high"]))
            .where(Finding.status.in_(["open", "in_progress"]))
        )
        open_critical = len(result2.scalars().all())

    overall_status = "approved" if open_critical == 0 else "conditional"

    return CertificationPackResponse(
        pack_id=f"CP-{payload.use_case_id[:8]}-{datetime.now(UTC).strftime('%Y%m%d')}",
        use_case_id=use_case.id,
        use_case_name=use_case.name,
        generated_at=datetime.now(UTC),
        artifact_ids=artifact_ids,
        sections=sections,
        overall_status=overall_status,
        risk_rating=use_case.risk_rating.value if use_case.risk_rating else "unknown",
        summary={
            "total_sections": len(sections),
            "open_critical_findings": open_critical,
            "certification_status": overall_status,
            "generated_by": "Control Tower Certification Engine v1.0",
        },
    )


@router.post("/generate-pdf")
async def generate_certification_pack_pdf_endpoint(
    payload: CertificationPackRequest, db: AsyncSession = Depends(get_db)
):
    """
    Generate and download the certification pack as a PDF.
    Calls the JSON endpoint internally, then renders to PDF via ReportLab.
    """
    # Reuse the JSON generation logic
    json_response = await generate_certification_pack(payload, db)
    pack_data = json_response.model_dump()

    # Render to PDF
    pdf_bytes = generate_certification_pack_pdf(pack_data)

    filename = f"CertPack_{pack_data['pack_id']}_{datetime.now(UTC).strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
