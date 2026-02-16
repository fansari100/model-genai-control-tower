"""
Regulatory Change Detector — semantic impact analysis engine.
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()


class Regulator(str, Enum):
    SEC = "SEC"
    FINRA = "FINRA"
    OCC = "OCC"
    FED = "Federal Reserve"
    CFPB = "CFPB"
    NIST = "NIST"
    STATE = "State Regulator"


class ImpactLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class AffectedArea(BaseModel):
    business_unit: str = Field(description="Affected business unit")
    function: str = Field(description="Specific function impacted")
    existing_control: str = Field(description="Current control that may need updating")
    gap_identified: bool = Field(False, description="Is there a control gap?")


class RegulatoryImpact(BaseModel):
    """Complete impact assessment for a regulatory change."""

    # Document metadata
    regulation_title: str = Field(description="Title of the regulatory update")
    regulator: Regulator
    publication_date: str | None = Field(None)
    effective_date: str | None = Field(None)
    document_type: str = Field(description="rule, guidance, enforcement, no-action letter, FAQ")

    # Impact assessment
    impact_level: ImpactLevel
    urgency: str = Field(description="immediate, 30_days, 90_days, next_review_cycle")
    summary: str = Field(description="2-3 sentence summary of the change")
    detailed_analysis: str = Field(description="Detailed analysis of implications for WM")

    # Affected areas
    affected_areas: list[AffectedArea] = Field(default_factory=list)
    affected_products: list[str] = Field(default_factory=list, description="Products affected")
    affected_models: list[str] = Field(default_factory=list, description="Models that may need recertification")

    # Required actions
    required_actions: list[str] = Field(default_factory=list)
    policy_updates_needed: list[str] = Field(default_factory=list)
    training_required: bool = Field(False)

    # AI/GenAI specific
    genai_implications: str | None = Field(None, description="Specific implications for GenAI use cases")
    model_risk_implications: str | None = Field(None, description="Implications for model risk management")

    # Metadata
    confidence_score: float = Field(0.0)
    similar_past_regulations: list[str] = Field(default_factory=list)


DETECTOR_SYSTEM_PROMPT = """You are a regulatory change analyst for Morgan Stanley Wealth Management.
Analyze the provided regulatory document and assess its impact on WM operations.

Context: Morgan Stanley WM provides brokerage, investment advisory, financial planning,
credit/lending, cash management, annuities/insurance, and stock plan administration.
The firm uses GenAI applications for internal Q&A, meeting summarization, document
analysis, and portfolio risk assessment.

Rules:
1. Assess impact level based on scope of affected operations and urgency.
2. Identify ALL affected business units, products, and existing controls.
3. Flag any implications for GenAI use cases or model risk management.
4. Recommend specific, actionable steps — not generic advice.
5. Note if the change triggers recertification of any models.
6. Consider both direct regulatory requirements and indirect operational impacts.
"""


async def analyze_regulatory_change(
    document_text: str,
    regulator: str = "auto",
    model: str = "gpt-5.2",
    api_key: str = "",
) -> RegulatoryImpact:
    """Analyze a regulatory document for WM impact."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()

    logger.info("regulatory_analysis_start", doc_length=len(document_text), model=model)

    try:
        response = await client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": DETECTOR_SYSTEM_PROMPT},
                {"role": "user", "content": f"Regulator hint: {regulator}\n\nRegulatory Document:\n{document_text[:10000]}"},
            ],
            response_format=RegulatoryImpact,
            temperature=0,
        )

        impact = response.choices[0].message.parsed
        if impact is None:
            raise ValueError("LLM returned no parsed output")

        logger.info(
            "regulatory_analysis_complete",
            title=impact.regulation_title,
            impact=impact.impact_level.value,
            affected_areas=len(impact.affected_areas),
        )

        return impact

    except Exception as e:
        logger.error("regulatory_analysis_failed", error=str(e))
        raise
