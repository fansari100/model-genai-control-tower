"""
Guardrails service – cascade classification architecture.

Implements the two-stage defense pattern:
1. Lightweight first-pass filters (fast, cheap)
2. Escalation to heavier classifiers / human review (accurate, expensive)

Aligned with Jan-2026 cascade defense architecture patterns.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger()


class ThreatLevel(str, Enum):
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    BLOCKED = "blocked"


class EscalationAction(str, Enum):
    PASS = "pass"
    ESCALATE_TO_CLASSIFIER = "escalate_to_classifier"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    BLOCK = "block"


@dataclass
class GuardrailResult:
    """Result of a guardrail check."""

    threat_level: ThreatLevel
    action: EscalationAction
    stage: str
    reason: str
    details: dict = field(default_factory=dict)
    confidence: float = 1.0


# ── Stage 1: Lightweight First-Pass Filters ──────────────────────────────────

# Common injection patterns (regex-based, fast)
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"you\s+are\s+now\s+.*(DAN|jailbreak|unrestricted)",
    r"system\s*:\s*you\s+are",
    r"<\|im_start\|>system",
    r"\[INST\].*\[/INST\]",
    r"```\s*(system|admin|root)",
    r"ignore\s+your\s+(rules|guidelines|constraints)",
    r"do\s+not\s+follow\s+your\s+(instructions|programming)",
    r"pretend\s+you\s+(are|have)\s+no\s+(rules|restrictions)",
]

# PII detection patterns (for output filtering)
PII_PATTERNS = {
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "account_number": r"\b\d{8,12}\b",
}

# Toxicity keywords (simplified – production uses ML classifier)
TOXICITY_KEYWORDS = [
    "kill", "harm", "illegal", "exploit", "hack", "weapon",
    "fraud", "steal", "extort", "blackmail", "launder",
]


def stage1_injection_check(text: str) -> GuardrailResult:
    """Fast regex-based injection detection."""
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            return GuardrailResult(
                threat_level=ThreatLevel.BLOCKED,
                action=EscalationAction.BLOCK,
                stage="stage1_injection",
                reason=f"Prompt injection pattern detected: {pattern}",
                confidence=0.85,
            )
    return GuardrailResult(
        threat_level=ThreatLevel.SAFE,
        action=EscalationAction.PASS,
        stage="stage1_injection",
        reason="No injection patterns detected",
    )


def stage1_pii_check(text: str) -> GuardrailResult:
    """Fast regex-based PII detection in outputs."""
    detected: list[str] = []
    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, text):
            detected.append(pii_type)

    if detected:
        return GuardrailResult(
            threat_level=ThreatLevel.SUSPICIOUS,
            action=EscalationAction.ESCALATE_TO_CLASSIFIER,
            stage="stage1_pii",
            reason=f"Potential PII detected: {', '.join(detected)}",
            details={"pii_types": detected},
            confidence=0.7,
        )
    return GuardrailResult(
        threat_level=ThreatLevel.SAFE,
        action=EscalationAction.PASS,
        stage="stage1_pii",
        reason="No PII patterns detected",
    )


def stage1_toxicity_check(text: str) -> GuardrailResult:
    """Fast keyword-based toxicity check."""
    text_lower = text.lower()
    found = [kw for kw in TOXICITY_KEYWORDS if kw in text_lower]

    if len(found) >= 3:
        return GuardrailResult(
            threat_level=ThreatLevel.BLOCKED,
            action=EscalationAction.BLOCK,
            stage="stage1_toxicity",
            reason=f"Multiple toxicity indicators: {found}",
            confidence=0.6,
        )
    elif found:
        return GuardrailResult(
            threat_level=ThreatLevel.SUSPICIOUS,
            action=EscalationAction.ESCALATE_TO_CLASSIFIER,
            stage="stage1_toxicity",
            reason=f"Potential toxicity indicators: {found}",
            details={"keywords": found},
            confidence=0.4,
        )
    return GuardrailResult(
        threat_level=ThreatLevel.SAFE,
        action=EscalationAction.PASS,
        stage="stage1_toxicity",
        reason="No toxicity indicators",
    )


# ── Stage 2: Heavy Classifier (OpenAI Moderation API) ────────────────────────

async def stage2_classify(text: str, context: str = "input") -> GuardrailResult:
    """
    Stage 2 heavy classifier – calls OpenAI Moderation API for high-confidence
    content safety classification. Only invoked when Stage 1 escalates.
    """
    import httpx
    from app.config import get_settings

    settings = get_settings()
    api_key = settings.openai_api_key

    if not api_key:
        logger.warning("stage2_no_api_key", context=context)
        # Fail-open only in non-production; fail-closed in production
        if settings.is_production:
            return GuardrailResult(
                threat_level=ThreatLevel.BLOCKED,
                action=EscalationAction.ESCALATE_TO_HUMAN,
                stage="stage2_classifier",
                reason="Moderation API unavailable in production — escalating to human review",
                confidence=0.0,
            )
        return GuardrailResult(
            threat_level=ThreatLevel.SAFE,
            action=EscalationAction.PASS,
            stage="stage2_classifier",
            reason="Moderation API key not configured — passing in non-production",
            confidence=0.5,
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/moderations",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"input": text},
            )
            resp.raise_for_status()
            data = resp.json()

        result = data["results"][0]
        flagged = result.get("flagged", False)
        categories = result.get("categories", {})
        scores = result.get("category_scores", {})

        # Find the highest-scoring flagged category
        flagged_categories = [cat for cat, val in categories.items() if val]
        max_score = max(scores.values()) if scores else 0.0

        if flagged:
            logger.warning(
                "stage2_content_flagged",
                context=context,
                categories=flagged_categories,
                max_score=f"{max_score:.3f}",
            )
            return GuardrailResult(
                threat_level=ThreatLevel.BLOCKED,
                action=EscalationAction.BLOCK,
                stage="stage2_classifier",
                reason=f"Content flagged by moderation API: {', '.join(flagged_categories)}",
                details={"categories": flagged_categories, "scores": scores},
                confidence=max_score,
            )

        logger.info("stage2_content_safe", context=context, max_score=f"{max_score:.3f}")
        return GuardrailResult(
            threat_level=ThreatLevel.SAFE,
            action=EscalationAction.PASS,
            stage="stage2_classifier",
            reason="Content passed moderation API check",
            confidence=1.0 - max_score,
        )

    except httpx.HTTPStatusError as e:
        logger.error("stage2_api_error", status=e.response.status_code, context=context)
        return GuardrailResult(
            threat_level=ThreatLevel.SUSPICIOUS,
            action=EscalationAction.ESCALATE_TO_HUMAN,
            stage="stage2_classifier",
            reason=f"Moderation API returned {e.response.status_code} — escalating to human",
            confidence=0.0,
        )
    except Exception as e:
        logger.error("stage2_exception", error=str(e), context=context)
        return GuardrailResult(
            threat_level=ThreatLevel.SUSPICIOUS,
            action=EscalationAction.ESCALATE_TO_HUMAN,
            stage="stage2_classifier",
            reason=f"Moderation API unreachable — escalating to human review",
            confidence=0.0,
        )


# ── Cascade Orchestrator ─────────────────────────────────────────────────────

async def run_cascade_guardrails(
    text: str,
    context: str = "input",  # "input" or "output"
    config: dict | None = None,
) -> list[GuardrailResult]:
    """
    Run the full cascade guardrail pipeline.

    Stage 1 (fast): regex/keyword checks
    Stage 2 (heavy): ML classifier (only if Stage 1 escalates)

    Returns list of all check results for logging/auditing.
    """
    results: list[GuardrailResult] = []

    # Stage 1 checks
    stage1_checks = [
        stage1_injection_check(text),
        stage1_pii_check(text),
        stage1_toxicity_check(text),
    ]
    results.extend(stage1_checks)

    # If any Stage 1 check blocks, stop immediately
    if any(r.action == EscalationAction.BLOCK for r in stage1_checks):
        logger.warning(
            "guardrail_blocked",
            context=context,
            blocking_stage=[r.stage for r in stage1_checks if r.action == EscalationAction.BLOCK],
        )
        return results

    # If any Stage 1 check escalates, run Stage 2
    needs_escalation = any(
        r.action == EscalationAction.ESCALATE_TO_CLASSIFIER for r in stage1_checks
    )

    if needs_escalation:
        stage2_result = await stage2_classify(text, context)
        results.append(stage2_result)

        if stage2_result.action == EscalationAction.BLOCK:
            logger.warning("guardrail_blocked_stage2", context=context)
        elif stage2_result.action == EscalationAction.ESCALATE_TO_HUMAN:
            logger.info("guardrail_human_escalation", context=context)

    return results


def get_final_action(results: list[GuardrailResult]) -> EscalationAction:
    """Get the most restrictive action from a list of guardrail results."""
    priority = {
        EscalationAction.BLOCK: 3,
        EscalationAction.ESCALATE_TO_HUMAN: 2,
        EscalationAction.ESCALATE_TO_CLASSIFIER: 1,
        EscalationAction.PASS: 0,
    }
    return max(results, key=lambda r: priority[r.action]).action
