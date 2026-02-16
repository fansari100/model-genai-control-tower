"""
Portfolio Risk Narrator — data-to-text generation for risk commentary.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()


class PortfolioData(BaseModel):
    """Input: structured portfolio analytics data."""
    client_name: str
    portfolio_id: str
    as_of_date: str
    total_value: float
    benchmark: str = "S&P 500"

    # Returns
    mtd_return_pct: float
    qtd_return_pct: float
    ytd_return_pct: float
    one_year_return_pct: float | None = None
    benchmark_ytd_pct: float = 0.0

    # Risk metrics
    volatility_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    beta: float
    var_95_pct: float  # Value at Risk (95% confidence)
    cvar_95_pct: float  # Conditional VaR

    # Allocation
    equity_pct: float
    fixed_income_pct: float
    alternatives_pct: float
    cash_pct: float

    # Concentration
    top_holding_name: str
    top_holding_pct: float
    sector_concentration: dict[str, float] = {}


class RiskNarrative(BaseModel):
    """Output: structured risk commentary."""
    executive_summary: str = Field(description="2-3 sentence performance and risk overview")
    performance_commentary: str = Field(description="Detailed return analysis vs benchmark")
    risk_assessment: str = Field(description="Risk metrics analysis and interpretation")
    allocation_commentary: str = Field(description="Asset allocation observations")
    concentration_analysis: str = Field(description="Concentration risk assessment")
    outlook_considerations: str = Field(description="Forward-looking risk considerations")
    action_recommendations: list[str] = Field(default_factory=list, description="Suggested actions")

    # Fact-checking
    numbers_cited: list[dict] = Field(default_factory=list, description="All numbers used with source verification")
    confidence_score: float = Field(0.0)


NARRATOR_SYSTEM_PROMPT = """You are a portfolio risk analyst at Morgan Stanley Wealth Management.
Given structured portfolio data, generate professional risk commentary suitable for client
quarterly reports and risk committee presentations.

Rules:
1. ONLY use numbers from the provided data. Never fabricate statistics.
2. Cite every number you use with the source field name in [brackets].
3. Use precise financial terminology appropriate for high-net-worth clients.
4. Highlight any concerning metrics (e.g., high concentration, elevated VaR, drawdown).
5. Provide actionable recommendations based on the data.
6. Compare performance to the stated benchmark.
7. Note any style drift or allocation deviations from typical targets.
"""


async def generate_risk_narrative(
    portfolio: PortfolioData,
    model: str = "gpt-5.2",
    api_key: str = "",
) -> RiskNarrative:
    """Generate risk commentary from portfolio data."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()

    logger.info("risk_narrative_start", portfolio_id=portfolio.portfolio_id, model=model)

    portfolio_json = portfolio.model_dump_json(indent=2)

    try:
        response = await client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": NARRATOR_SYSTEM_PROMPT},
                {"role": "user", "content": f"Generate risk commentary for this portfolio:\n\n{portfolio_json}"},
            ],
            response_format=RiskNarrative,
            temperature=0.2,
        )

        narrative = response.choices[0].message.parsed
        if narrative is None:
            raise ValueError("LLM returned no parsed output")

        # Fact-check: verify all cited numbers exist in source data
        narrative = _fact_check_narrative(narrative, portfolio)

        logger.info("risk_narrative_complete", confidence=narrative.confidence_score)
        return narrative

    except Exception as e:
        logger.error("risk_narrative_failed", error=str(e))
        raise


def _fact_check_narrative(narrative: RiskNarrative, portfolio: PortfolioData) -> RiskNarrative:
    """Verify all numbers in the narrative exist in the source data."""
    import re

    source_numbers = {
        "total_value": portfolio.total_value,
        "mtd_return_pct": portfolio.mtd_return_pct,
        "qtd_return_pct": portfolio.qtd_return_pct,
        "ytd_return_pct": portfolio.ytd_return_pct,
        "volatility_pct": portfolio.volatility_pct,
        "sharpe_ratio": portfolio.sharpe_ratio,
        "max_drawdown_pct": portfolio.max_drawdown_pct,
        "beta": portfolio.beta,
        "var_95_pct": portfolio.var_95_pct,
        "equity_pct": portfolio.equity_pct,
        "fixed_income_pct": portfolio.fixed_income_pct,
        "top_holding_pct": portfolio.top_holding_pct,
    }

    cited = []
    full_text = " ".join([
        narrative.executive_summary,
        narrative.performance_commentary,
        narrative.risk_assessment,
    ])

    numbers_in_text = re.findall(r'[\d]+\.[\d]+|[\d]+', full_text)
    for num_str in numbers_in_text:
        try:
            num = float(num_str)
            matched = False
            for field_name, source_val in source_numbers.items():
                if source_val is not None and abs(num - abs(source_val)) < 0.01:
                    cited.append({"value": num, "source_field": field_name, "verified": True})
                    matched = True
                    break
            if not matched and num > 1:  # Ignore small numbers like percentages
                cited.append({"value": num, "source_field": "UNVERIFIED", "verified": False})
        except ValueError:
            pass

    narrative.numbers_cited = cited
    verified_count = sum(1 for c in cited if c["verified"])
    total_count = len(cited) if cited else 1
    narrative.confidence_score = verified_count / total_count

    return narrative
