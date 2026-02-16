"""
Document Intelligence Extractor — structured data extraction from financial documents.

Uses LLM with Pydantic structured output to extract:
  - Fund metadata (name, CUSIP, ticker, inception date, expense ratio)
  - Risk metrics (standard deviation, Sharpe ratio, max drawdown, beta)
  - Holdings breakdown (top 10 holdings with weights)
  - Fee structure (management fee, 12b-1, load, redemption)
  - Regulatory flags (leverage, derivatives usage, concentration)
"""

from __future__ import annotations

import json
from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()


# ── Structured Output Schemas ────────────────────────────────────────────────

class AssetClass(str, Enum):
    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    ALTERNATIVES = "alternatives"
    MULTI_ASSET = "multi_asset"
    MONEY_MARKET = "money_market"
    REAL_ESTATE = "real_estate"
    COMMODITIES = "commodities"


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Holding(BaseModel):
    """Individual holding within a fund."""
    name: str = Field(description="Security name")
    ticker: Optional[str] = Field(None, description="Ticker symbol if available")
    weight_pct: float = Field(description="Portfolio weight as percentage")
    sector: Optional[str] = Field(None, description="GICS sector")


class FeeStructure(BaseModel):
    """Fee breakdown for a fund."""
    management_fee_pct: Optional[float] = Field(None, description="Annual management fee %")
    expense_ratio_pct: Optional[float] = Field(None, description="Total expense ratio %")
    twelve_b1_fee_pct: Optional[float] = Field(None, description="12b-1 distribution fee %")
    front_load_pct: Optional[float] = Field(None, description="Front-end sales load %")
    back_load_pct: Optional[float] = Field(None, description="Back-end deferred sales charge %")
    redemption_fee_pct: Optional[float] = Field(None, description="Short-term redemption fee %")


class RiskMetrics(BaseModel):
    """Quantitative risk metrics extracted from the document."""
    standard_deviation_pct: Optional[float] = Field(None, description="Annualized standard deviation %")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    max_drawdown_pct: Optional[float] = Field(None, description="Maximum drawdown %")
    beta: Optional[float] = Field(None, description="Beta vs benchmark")
    alpha_pct: Optional[float] = Field(None, description="Alpha vs benchmark %")
    r_squared: Optional[float] = Field(None, description="R-squared vs benchmark")
    tracking_error_pct: Optional[float] = Field(None, description="Tracking error %")


class RegulatoryFlags(BaseModel):
    """Regulatory and compliance flags extracted from the document."""
    uses_leverage: bool = Field(False, description="Fund uses leverage")
    uses_derivatives: bool = Field(False, description="Fund uses derivatives")
    concentrated_portfolio: bool = Field(False, description="Top 10 holdings > 50% of portfolio")
    sec_registered: bool = Field(True, description="Registered with SEC")
    erisa_eligible: bool = Field(False, description="Eligible for ERISA plans")
    esg_integrated: bool = Field(False, description="ESG factors integrated into process")


class DocumentExtraction(BaseModel):
    """Complete structured extraction from a financial document."""

    # Metadata
    document_type: str = Field(description="Type: prospectus, fact_sheet, ips, commentary")
    fund_name: str = Field(description="Full legal fund name")
    fund_family: Optional[str] = Field(None, description="Fund family / manager")
    ticker: Optional[str] = Field(None, description="Primary ticker symbol")
    cusip: Optional[str] = Field(None, description="CUSIP identifier")
    inception_date: Optional[str] = Field(None, description="Fund inception date")
    benchmark: Optional[str] = Field(None, description="Primary benchmark index")
    asset_class: AssetClass = Field(description="Primary asset class")
    risk_level: RiskLevel = Field(description="Overall risk assessment")

    # Quantitative
    aum_millions: Optional[float] = Field(None, description="Assets under management in $M")
    ytd_return_pct: Optional[float] = Field(None, description="Year-to-date return %")
    one_year_return_pct: Optional[float] = Field(None, description="1-year return %")
    three_year_return_pct: Optional[float] = Field(None, description="3-year annualized return %")
    five_year_return_pct: Optional[float] = Field(None, description="5-year annualized return %")

    # Structured components
    risk_metrics: RiskMetrics = Field(default_factory=RiskMetrics)
    fee_structure: FeeStructure = Field(default_factory=FeeStructure)
    top_holdings: list[Holding] = Field(default_factory=list, description="Top holdings")
    regulatory_flags: RegulatoryFlags = Field(default_factory=RegulatoryFlags)

    # Investment process
    investment_objective: Optional[str] = Field(None, description="Stated investment objective")
    investment_strategy: Optional[str] = Field(None, description="Strategy description")
    key_risks: list[str] = Field(default_factory=list, description="Key risk factors")

    # Extraction metadata
    confidence_score: float = Field(0.0, description="Overall extraction confidence 0-1")
    extraction_warnings: list[str] = Field(default_factory=list)


# ── Extraction Engine ────────────────────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """You are a financial document analysis engine for Morgan Stanley
Wealth Management. Extract structured data from the provided financial document text.

Rules:
1. Extract ONLY information explicitly stated in the document. Do not infer or estimate.
2. If a field is not present in the document, leave it as null.
3. For percentages, provide the numeric value (e.g., 1.25 for 1.25%).
4. Flag any inconsistencies or unusual values in extraction_warnings.
5. Set confidence_score based on how much of the schema you could fill (0.0-1.0).
"""


async def extract_document(
    document_text: str,
    document_type: str = "auto",
    model: str = "gpt-5.2",
    api_key: str = "",
) -> DocumentExtraction:
    """
    Extract structured financial data from a document using LLM structured output.

    Args:
        document_text: The raw text of the financial document.
        document_type: Hint about document type (prospectus, fact_sheet, etc.)
        model: LLM model to use.
        api_key: OpenAI API key.

    Returns:
        DocumentExtraction with all extracted fields.
    """
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()

    logger.info("document_extraction_start", doc_length=len(document_text), model=model)

    try:
        response = await client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Document type hint: {document_type}\n\nDocument text:\n{document_text[:12000]}"},
            ],
            response_format=DocumentExtraction,
            temperature=0,
        )

        extraction = response.choices[0].message.parsed
        if extraction is None:
            raise ValueError("LLM returned no parsed output")

        # Post-processing validation
        extraction = _validate_extraction(extraction)

        logger.info(
            "document_extraction_complete",
            fund_name=extraction.fund_name,
            confidence=extraction.confidence_score,
            warnings=len(extraction.extraction_warnings),
        )

        return extraction

    except Exception as e:
        logger.error("document_extraction_failed", error=str(e))
        raise


def _validate_extraction(extraction: DocumentExtraction) -> DocumentExtraction:
    """Apply business rules validation to the extraction."""
    warnings = list(extraction.extraction_warnings)

    # Validate expense ratio vs management fee
    if (extraction.fee_structure.expense_ratio_pct and
            extraction.fee_structure.management_fee_pct and
            extraction.fee_structure.expense_ratio_pct < extraction.fee_structure.management_fee_pct):
        warnings.append("Expense ratio is less than management fee — possible extraction error")

    # Validate concentration flag
    if extraction.top_holdings:
        total_weight = sum(h.weight_pct for h in extraction.top_holdings[:10])
        if total_weight > 50 and not extraction.regulatory_flags.concentrated_portfolio:
            extraction.regulatory_flags.concentrated_portfolio = True
            warnings.append(f"Auto-flagged concentrated portfolio: top holdings = {total_weight:.1f}%")

    # Validate Sharpe ratio range
    if extraction.risk_metrics.sharpe_ratio and abs(extraction.risk_metrics.sharpe_ratio) > 5:
        warnings.append(f"Unusual Sharpe ratio: {extraction.risk_metrics.sharpe_ratio}")

    # Validate beta range
    if extraction.risk_metrics.beta and (extraction.risk_metrics.beta < -2 or extraction.risk_metrics.beta > 5):
        warnings.append(f"Unusual beta: {extraction.risk_metrics.beta}")

    extraction.extraction_warnings = warnings
    return extraction
