"""
PII redaction utilities – redact sensitive data before logging/storing.

Uses Microsoft Presidio for entity recognition with regex fallback.
Presidio provides ML-based NER for names, addresses, and complex patterns
that regex alone cannot reliably detect.
"""

from __future__ import annotations

import re
from functools import lru_cache

import structlog

logger = structlog.get_logger()

# ── Regex fallback patterns ──────────────────────────────────────────────────
_REGEX_RULES = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN_REDACTED]"),
    (r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "[CARD_REDACTED]"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_REDACTED]"),
    (r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE_REDACTED]"),
    (r"\baccount\s*#?\s*\d{8,12}\b", "[ACCOUNT_REDACTED]"),
]


@lru_cache(maxsize=1)
def _get_presidio_analyzer():
    """Lazy-load Presidio analyzer with caching."""
    try:
        from presidio_analyzer import AnalyzerEngine

        analyzer = AnalyzerEngine()
        logger.info("presidio_analyzer_loaded")
        return analyzer
    except ImportError:
        logger.debug("presidio_not_installed_using_regex_fallback")
        return None
    except Exception as e:
        logger.warning("presidio_init_failed", error=str(e))
        return None


@lru_cache(maxsize=1)
def _get_presidio_anonymizer():
    """Lazy-load Presidio anonymizer with caching."""
    try:
        from presidio_anonymizer import AnonymizerEngine

        return AnonymizerEngine()
    except ImportError:
        return None
    except Exception as e:
        logger.warning("presidio_anonymizer_init_failed", error=str(e))
        return None


def redact_pii(text: str, language: str = "en") -> str:
    """
    Redact PII from text using Presidio (if available) or regex fallback.

    Presidio detects: PERSON, EMAIL_ADDRESS, PHONE_NUMBER, CREDIT_CARD,
    US_SSN, US_BANK_NUMBER, IP_ADDRESS, LOCATION, etc.
    """
    analyzer = _get_presidio_analyzer()
    anonymizer = _get_presidio_anonymizer()

    if analyzer and anonymizer:
        try:
            results = analyzer.analyze(
                text=text,
                language=language,
                entities=[
                    "PERSON",
                    "EMAIL_ADDRESS",
                    "PHONE_NUMBER",
                    "CREDIT_CARD",
                    "US_SSN",
                    "US_BANK_NUMBER",
                    "IP_ADDRESS",
                    "LOCATION",
                    "DATE_TIME",
                    "NRP",
                    "MEDICAL_LICENSE",
                    "URL",
                ],
                score_threshold=0.5,
            )
            if results:
                anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
                return anonymized.text
            return text
        except Exception as e:
            logger.warning("presidio_redaction_failed", error=str(e))
            # Fall through to regex

    # Regex fallback
    for pattern, replacement in _REGEX_RULES:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def redact_dict_values(data: dict, keys_to_redact: set[str] | None = None) -> dict:
    """Recursively redact string values in a dictionary."""
    if keys_to_redact is None:
        keys_to_redact = {
            "prompt",
            "output",
            "input",
            "response",
            "message",
            "content",
            "text",
            "transcript",
            "notes",
            "email_body",
        }

    result = {}
    for key, value in data.items():
        if isinstance(value, str) and key.lower() in keys_to_redact:
            result[key] = redact_pii(value)
        elif isinstance(value, dict):
            result[key] = redact_dict_values(value, keys_to_redact)
        elif isinstance(value, list):
            result[key] = [
                redact_dict_values(v, keys_to_redact) if isinstance(v, dict) else v for v in value
            ]
        else:
            result[key] = value
    return result
