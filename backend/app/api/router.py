"""Central API router – aggregates all v1 endpoint routers."""

from fastapi import APIRouter

from app.api.v1 import (
    approvals,
    certifications,
    dashboard,
    evaluations,
    evidence,
    findings,
    model_demos,
    models,
    monitoring,
    tools,
    use_cases,
    vendors,
)

api_router = APIRouter()

api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(vendors.router, prefix="/vendors", tags=["Vendors"])
api_router.include_router(models.router, prefix="/models", tags=["Models"])
api_router.include_router(tools.router, prefix="/tools", tags=["Tools & EUCs"])
api_router.include_router(use_cases.router, prefix="/use-cases", tags=["GenAI Use Cases"])
api_router.include_router(evaluations.router, prefix="/evaluations", tags=["Evaluations"])
api_router.include_router(findings.router, prefix="/findings", tags=["Findings"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["Approvals"])
api_router.include_router(evidence.router, prefix="/evidence", tags=["Evidence"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])
api_router.include_router(certifications.router, prefix="/certifications", tags=["Certifications"])
api_router.include_router(model_demos.router, prefix="/model-demos", tags=["GenAI Model Demos"])
