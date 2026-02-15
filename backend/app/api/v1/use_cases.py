"""GenAI Use Case CRUD + intake / risk assessment endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentUser, get_current_user, require_write
from app.database import get_db
from app.models.genai_use_case import (
    DataClassification,
    GenAIUseCase,
    RiskRating,
    UseCaseCategory,
    UseCaseModelLink,
    UseCaseStatus,
    UseCaseToolLink,
)
from app.schemas.common import PaginatedResponse
from app.schemas.genai_use_case import (
    UseCaseCreate,
    UseCaseIntakeRequest,
    UseCaseIntakeResponse,
    UseCaseListResponse,
    UseCaseResponse,
    UseCaseUpdate,
)
from app.services.audit_events import emit_use_case_intake
from app.services.risk_rating import compute_risk_rating

router = APIRouter()


@router.get("", response_model=PaginatedResponse[UseCaseListResponse])
async def list_use_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    category: UseCaseCategory | None = None,
    status: UseCaseStatus | None = None,
    risk_rating: RiskRating | None = None,
    data_classification: DataClassification | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all GenAI use cases with filtering."""
    query = select(GenAIUseCase).where(GenAIUseCase.is_deleted == False)  # noqa: E712
    count_query = select(func.count()).select_from(GenAIUseCase).where(
        GenAIUseCase.is_deleted == False  # noqa: E712
    )

    if search:
        query = query.where(GenAIUseCase.name.ilike(f"%{search}%"))
        count_query = count_query.where(GenAIUseCase.name.ilike(f"%{search}%"))
    if category:
        query = query.where(GenAIUseCase.category == category)
        count_query = count_query.where(GenAIUseCase.category == category)
    if status:
        query = query.where(GenAIUseCase.status == status)
        count_query = count_query.where(GenAIUseCase.status == status)
    if risk_rating:
        query = query.where(GenAIUseCase.risk_rating == risk_rating)
        count_query = count_query.where(GenAIUseCase.risk_rating == risk_rating)
    if data_classification:
        query = query.where(GenAIUseCase.data_classification == data_classification)
        count_query = count_query.where(
            GenAIUseCase.data_classification == data_classification
        )

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.offset(offset).limit(page_size).order_by(GenAIUseCase.created_at.desc())
    )
    use_cases = result.scalars().all()

    return PaginatedResponse(
        items=[UseCaseListResponse.model_validate(uc) for uc in use_cases],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("", response_model=UseCaseResponse, status_code=201)
async def create_use_case(payload: UseCaseCreate, db: AsyncSession = Depends(get_db)):
    """Create a new GenAI use case."""
    data = payload.model_dump(exclude={"model_ids", "tool_ids"})
    use_case = GenAIUseCase(**data)
    db.add(use_case)
    await db.flush()

    # Link models
    if payload.model_ids:
        for mid in payload.model_ids:
            link = UseCaseModelLink(use_case_id=use_case.id, model_id=mid)
            db.add(link)

    # Link tools
    if payload.tool_ids:
        for tid in payload.tool_ids:
            link = UseCaseToolLink(use_case_id=use_case.id, tool_id=tid)
            db.add(link)

    await db.flush()
    await db.refresh(use_case)
    return UseCaseResponse.model_validate(use_case)


@router.get("/{use_case_id}", response_model=UseCaseResponse)
async def get_use_case(use_case_id: str, db: AsyncSession = Depends(get_db)):
    use_case = await db.get(GenAIUseCase, use_case_id)
    if not use_case or use_case.is_deleted:
        raise HTTPException(status_code=404, detail="Use case not found")
    return UseCaseResponse.model_validate(use_case)


@router.patch("/{use_case_id}", response_model=UseCaseResponse)
async def update_use_case(
    use_case_id: str, payload: UseCaseUpdate, db: AsyncSession = Depends(get_db)
):
    use_case = await db.get(GenAIUseCase, use_case_id)
    if not use_case or use_case.is_deleted:
        raise HTTPException(status_code=404, detail="Use case not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(use_case, key, value)

    await db.flush()
    await db.refresh(use_case)
    return UseCaseResponse.model_validate(use_case)


@router.delete("/{use_case_id}", status_code=204)
async def delete_use_case(use_case_id: str, db: AsyncSession = Depends(get_db)):
    use_case = await db.get(GenAIUseCase, use_case_id)
    if not use_case or use_case.is_deleted:
        raise HTTPException(status_code=404, detail="Use case not found")
    use_case.is_deleted = True
    await db.flush()


@router.post("/intake", response_model=UseCaseIntakeResponse, status_code=201)
async def intake_use_case(
    payload: UseCaseIntakeRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_write),
):
    """
    Stage 0: Intake & Classification.
    Creates a use case, computes risk rating, determines required test suites,
    identifies required approvals and committee path.
    """
    # Compute risk rating
    risk_result = compute_risk_rating(
        data_classification=payload.data_classification,
        handles_pii=payload.handles_pii,
        client_facing=payload.client_facing,
        uses_agents=payload.uses_agents,
        uses_tools=payload.uses_tools,
        uses_memory=payload.uses_memory,
        uses_rag=payload.uses_rag,
        category=payload.category,
    )

    # Create the use case
    use_case = GenAIUseCase(
        name=payload.name,
        description=payload.description,
        category=payload.category,
        owner=payload.owner,
        business_unit=payload.business_unit,
        sponsor=payload.sponsor,
        data_classification=payload.data_classification,
        handles_pii=payload.handles_pii,
        client_facing=payload.client_facing,
        uses_rag=payload.uses_rag,
        uses_agents=payload.uses_agents,
        uses_tools=payload.uses_tools,
        uses_memory=payload.uses_memory,
        risk_rating=risk_result["risk_rating"],
        required_test_suites=risk_result["required_test_suites"],
        status=UseCaseStatus.INTAKE,
        committee_path=risk_result["committee_path"],
        nist_governance_controls=risk_result.get("nist_considerations", {}),
        owasp_llm_top10_risks={"applicable_risks": risk_result.get("owasp_llm_risks", [])},
        owasp_agentic_top10_risks={"applicable_risks": risk_result.get("owasp_agentic_risks", [])},
        iso42001_phase="plan",
    )
    db.add(use_case)
    await db.flush()

    # Link models and tools
    if payload.model_ids:
        for mid in payload.model_ids:
            db.add(UseCaseModelLink(use_case_id=use_case.id, model_id=mid))
    if payload.tool_ids:
        for tid in payload.tool_ids:
            db.add(UseCaseToolLink(use_case_id=use_case.id, tool_id=tid))

    await db.flush()
    await db.refresh(use_case)

    # Emit audit event
    await emit_use_case_intake(use_case.id, risk_result["risk_rating"].value, user.username)

    return UseCaseIntakeResponse(
        use_case_id=use_case.id,
        risk_rating=risk_result["risk_rating"],
        risk_score=risk_result["risk_score"],
        risk_factors=risk_result["risk_factors"],
        required_test_suites=risk_result["required_test_suites"],
        required_approvals=risk_result["required_approvals"],
        committee_path=risk_result["committee_path"],
        nist_considerations=risk_result.get("nist_considerations", {}),
        owasp_llm_risks=risk_result.get("owasp_llm_risks", []),
        owasp_agentic_risks=risk_result.get("owasp_agentic_risks", []),
        estimated_certification_days=risk_result.get("estimated_days", 14),
    )
