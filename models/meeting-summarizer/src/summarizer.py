"""
Meeting Summarizer Engine — structured summarization with compliance awareness.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()


class ComplianceFlag(str, Enum):
    SUITABILITY_CONCERN = "suitability_concern"
    MISSING_DISCLOSURE = "missing_disclosure"
    CLIENT_COMPLAINT = "client_complaint"
    CONCENTRATION_RISK = "concentration_risk"
    OUTSIDE_BUSINESS = "outside_business"
    GIFT_ENTERTAINMENT = "gift_entertainment"
    SENIOR_INVESTOR = "senior_investor"
    PII_EXPOSED = "pii_exposed"


class ActionItem(BaseModel):
    description: str = Field(description="What needs to be done")
    owner: str = Field(description="Who is responsible (advisor, client, operations, etc.)")
    due_date: Optional[str] = Field(None, description="Target completion date if mentioned")
    priority: str = Field("normal", description="Priority: high, normal, low")


class ComplianceCheck(BaseModel):
    flag: ComplianceFlag
    description: str
    severity: str = Field("medium", description="low, medium, high")
    evidence: str = Field(description="Quote from transcript supporting this flag")


class MeetingSummary(BaseModel):
    """Complete structured output from meeting summarization."""

    # Summary
    summary: str = Field(description="2-3 sentence meeting overview")
    key_discussion_points: list[str] = Field(description="Bulleted list of topics discussed")
    action_items: list[ActionItem] = Field(default_factory=list)

    # Participants
    advisor_name: Optional[str] = Field(None)
    client_name: Optional[str] = Field(None)
    other_participants: list[str] = Field(default_factory=list)

    # Meeting metadata
    meeting_date: Optional[str] = Field(None)
    meeting_duration_minutes: Optional[int] = Field(None)
    meeting_type: str = Field("review", description="review, onboarding, planning, ad_hoc")

    # Financial details discussed
    portfolio_value_mentioned: Optional[float] = Field(None)
    asset_allocation_discussed: Optional[dict] = Field(None)
    products_discussed: list[str] = Field(default_factory=list)
    risk_tolerance_mentioned: Optional[str] = Field(None)

    # Compliance
    compliance_flags: list[ComplianceCheck] = Field(default_factory=list)
    client_consent_obtained: bool = Field(False, description="Did client provide consent for note-taking")

    # Draft email
    follow_up_email_draft: Optional[str] = Field(None, description="Draft follow-up email to client")

    # Metadata
    confidence_score: float = Field(0.0)
    pii_detected: list[str] = Field(default_factory=list, description="Types of PII found in transcript")


SUMMARIZER_SYSTEM_PROMPT = """You are a meeting summarization assistant for Morgan Stanley
Wealth Management advisors. Given a meeting transcript, produce a comprehensive structured summary.

Rules:
1. Include ALL factual details from the transcript (numbers, dates, names, account details).
2. Do NOT hallucinate or add information not in the transcript.
3. Flag ANY compliance-sensitive topics (suitability, disclosures, complaints, gifts, senior investors).
4. Draft a professional follow-up email that requires HUMAN REVIEW before sending.
5. Identify all PII types present (names, account numbers, SSNs, etc.).
6. If client consent for note-taking was mentioned, set client_consent_obtained = true.
7. Set confidence_score based on transcript clarity and completeness (0.0-1.0).
"""


async def summarize_meeting(
    transcript: str,
    model: str = "gpt-5.2",
    api_key: str = "",
) -> MeetingSummary:
    """
    Summarize a client meeting transcript into structured output.

    Args:
        transcript: Raw meeting transcript text.
        model: LLM model to use.
        api_key: OpenAI API key.

    Returns:
        MeetingSummary with all structured fields.
    """
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()

    logger.info("meeting_summarization_start", transcript_length=len(transcript), model=model)

    try:
        response = await client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": SUMMARIZER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Meeting Transcript:\n\n{transcript}"},
            ],
            response_format=MeetingSummary,
            temperature=0,
        )

        summary = response.choices[0].message.parsed
        if summary is None:
            raise ValueError("LLM returned no parsed output")

        # Post-processing: PII detection
        summary = _detect_pii(summary, transcript)

        logger.info(
            "meeting_summarization_complete",
            action_items=len(summary.action_items),
            compliance_flags=len(summary.compliance_flags),
            confidence=summary.confidence_score,
        )

        return summary

    except Exception as e:
        logger.error("meeting_summarization_failed", error=str(e))
        raise


def _detect_pii(summary: MeetingSummary, transcript: str) -> MeetingSummary:
    """Detect PII types in the transcript using regex patterns."""
    import re

    pii_types = []
    patterns = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "account_number": r"\b\d{8,12}\b",
        "phone": r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "dollar_amount": r"\$[\d,]+(?:\.\d{2})?",
    }

    for pii_type, pattern in patterns.items():
        if re.search(pattern, transcript, re.IGNORECASE):
            pii_types.append(pii_type)

    summary.pii_detected = pii_types

    if "ssn" in pii_types or "account_number" in pii_types:
        summary.compliance_flags.append(ComplianceCheck(
            flag=ComplianceFlag.PII_EXPOSED,
            description="Sensitive PII detected in transcript — ensure redaction before storage",
            severity="high",
            evidence=f"PII types detected: {', '.join(pii_types)}",
        ))

    return summary
