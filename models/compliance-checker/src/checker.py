"""
Client Communication Compliance Checker — pre-send screening engine.
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()


class ViolationType(str, Enum):
    MISLEADING_PERFORMANCE = "misleading_performance"
    PROMISSORY_LANGUAGE = "promissory_language"
    MISSING_DISCLOSURE = "missing_disclosure"
    UNSUITABLE_RECOMMENDATION = "unsuitable_recommendation"
    PII_IN_EXTERNAL = "pii_in_external_communication"
    UNBALANCED_PRESENTATION = "unbalanced_presentation"
    CHERRY_PICKED_TIMEFRAME = "cherry_picked_timeframe"
    TESTIMONIAL_VIOLATION = "testimonial_violation"
    SOCIAL_MEDIA_VIOLATION = "social_media_violation"
    UNAPPROVED_CONTENT = "unapproved_content"


class Violation(BaseModel):
    violation_type: ViolationType
    severity: str = Field(description="high, medium, low")
    description: str = Field(description="What the violation is")
    evidence: str = Field(description="Exact quote from the communication that violates")
    regulation: str = Field(description="Specific rule violated (e.g., FINRA Rule 2210)")
    suggested_fix: str = Field(description="How to fix the violation")


class ComplianceDecision(str, Enum):
    APPROVED = "approved"
    REQUIRES_CHANGES = "requires_changes"
    REJECTED = "rejected"
    ESCALATE = "escalate"


class ClientContext(BaseModel):
    """Context about the client for suitability assessment."""
    client_type: str = Field("retail", description="retail, institutional, qualified_purchaser")
    risk_tolerance: str = Field("moderate", description="conservative, moderate, aggressive")
    investment_experience: str = Field("intermediate", description="novice, intermediate, sophisticated")
    age: int | None = Field(None)
    is_senior: bool = Field(False, description="Age 65+ or designated as senior investor")
    account_type: str = Field("brokerage", description="brokerage, advisory, ira, trust")


class ComplianceReport(BaseModel):
    """Complete compliance screening result."""

    decision: ComplianceDecision
    overall_risk_score: float = Field(description="0.0 (clean) to 1.0 (critical violations)")

    violations: list[Violation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list, description="Non-blocking warnings")

    # Required additions
    required_disclosures: list[str] = Field(default_factory=list, description="Disclosures that must be added")
    suggested_revisions: list[str] = Field(default_factory=list, description="Recommended text changes")

    # Analysis
    communication_type: str = Field(description="email, letter, proposal, social_media, presentation")
    contains_performance_data: bool = Field(False)
    contains_recommendations: bool = Field(False)
    contains_projections: bool = Field(False)

    # Regulatory mapping
    applicable_rules: list[str] = Field(default_factory=list, description="e.g., FINRA 2210, SEC 206(4)")

    confidence_score: float = Field(0.0)


CHECKER_SYSTEM_PROMPT = """You are a compliance reviewer for Morgan Stanley Wealth Management
advisor communications. Screen the provided draft communication for regulatory violations.

Key regulations:
- FINRA Rule 2210 (Communications with the Public): Fair, balanced, not misleading
- FINRA Rule 2111 (Suitability): Recommendations must be suitable for the client
- SEC Rule 206(4) (Investment Advisers Act): No fraud or deceit
- SEC Marketing Rule (284.206(4)-1): Performance advertising requirements
- FINRA Rule 3110 (Supervision): Written supervisory procedures

Common violations to check:
1. Promissory language: "guaranteed", "risk-free", "can't lose", "will definitely"
2. Cherry-picked performance: Only showing best timeframe, omitting poor periods
3. Missing disclosures: Past performance disclaimer, risk warnings, fee disclosures
4. Unbalanced presentation: Only upside mentioned without risks
5. Unsuitable recommendations: Products inappropriate for client's profile
6. PII exposure: SSNs, account numbers in external communications
7. Testimonial issues: Client testimonials without required disclosures

Rules:
1. Flag EVERY potential violation with the exact violating text.
2. Cite the specific regulation for each violation.
3. Provide a concrete fix for each violation.
4. Consider the client context (risk tolerance, experience, age, account type).
5. For senior investors (65+), apply heightened scrutiny per FINRA senior guidelines.
"""


async def check_compliance(
    communication_text: str,
    client_context: ClientContext | None = None,
    model: str = "gpt-5.2",
    api_key: str = "",
) -> ComplianceReport:
    """Screen a client communication for compliance violations."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()

    context_json = (client_context or ClientContext()).model_dump_json(indent=2)

    logger.info("compliance_check_start", text_length=len(communication_text), model=model)

    try:
        response = await client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": CHECKER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Client Context:\n{context_json}\n\nDraft Communication:\n{communication_text}"},
            ],
            response_format=ComplianceReport,
            temperature=0,
        )

        report = response.choices[0].message.parsed
        if report is None:
            raise ValueError("LLM returned no parsed output")

        # Post-processing: rule-based checks that LLM might miss
        report = _rule_based_checks(report, communication_text, client_context)

        logger.info(
            "compliance_check_complete",
            decision=report.decision.value,
            violations=len(report.violations),
            risk_score=report.overall_risk_score,
        )

        return report

    except Exception as e:
        logger.error("compliance_check_failed", error=str(e))
        raise


def _rule_based_checks(
    report: ComplianceReport,
    text: str,
    client_context: ClientContext | None,
) -> ComplianceReport:
    """Apply deterministic rule-based compliance checks."""
    import re

    text_lower = text.lower()

    # Promissory language (regex — catches what LLM might miss)
    promissory_patterns = [
        r"\bguarantee[ds]?\b", r"\brisk[\s-]?free\b", r"\bcan'?t lose\b",
        r"\bwill definitely\b", r"\bsure thing\b", r"\bno risk\b",
        r"\bcertain to\b", r"\bassured\b",
    ]
    for pattern in promissory_patterns:
        match = re.search(pattern, text_lower)
        if match:
            already_flagged = any(
                v.violation_type == ViolationType.PROMISSORY_LANGUAGE
                and match.group().lower() in v.evidence.lower()
                for v in report.violations
            )
            if not already_flagged:
                report.violations.append(Violation(
                    violation_type=ViolationType.PROMISSORY_LANGUAGE,
                    severity="high",
                    description=f"Promissory language detected: '{match.group()}'",
                    evidence=text[max(0, match.start()-20):match.end()+20],
                    regulation="FINRA Rule 2210(d)(1)(B)",
                    suggested_fix=f"Remove '{match.group()}' and replace with balanced language acknowledging risks",
                ))

    # PII check
    ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"
    if re.search(ssn_pattern, text):
        report.violations.append(Violation(
            violation_type=ViolationType.PII_IN_EXTERNAL,
            severity="high",
            description="Social Security Number detected in external communication",
            evidence="[SSN REDACTED]",
            regulation="Reg S-P (Privacy of Consumer Financial Information)",
            suggested_fix="Remove all SSN references from external communications",
        ))

    # Performance without disclaimer
    if report.contains_performance_data:
        has_disclaimer = any(phrase in text_lower for phrase in [
            "past performance", "no guarantee", "not indicative", "may lose value",
        ])
        if not has_disclaimer:
            report.required_disclosures.append(
                "Past performance is not indicative of future results. Investments may lose value."
            )

    # Senior investor heightened scrutiny
    if client_context and client_context.is_senior and report.contains_recommendations:
        report.warnings.append(
            "SENIOR INVESTOR: This communication contains recommendations to a senior investor. "
            "Heightened supervision required per FINRA Regulatory Notice 07-43."
        )

    # Recalculate decision based on all violations
    high_violations = sum(1 for v in report.violations if v.severity == "high")
    if high_violations >= 2:
        report.decision = ComplianceDecision.REJECTED
    elif high_violations == 1 or len(report.violations) >= 3:
        report.decision = ComplianceDecision.REQUIRES_CHANGES
    elif len(report.violations) == 0 and len(report.warnings) == 0:
        report.decision = ComplianceDecision.APPROVED

    # Risk score
    report.overall_risk_score = min(1.0, len(report.violations) * 0.2 + high_violations * 0.3)

    return report
