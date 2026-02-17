"""
Live GenAI Model Demo Endpoints — GPT-5.2 powered.

5 vendor models with real inference:
  1. Document Intelligence (extraction)
  2. Meeting Summarizer
  3. Portfolio Risk Narrator
  4. Regulatory Change Detector
  5. Compliance Checker (fully rule-based, no API key needed)
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()


# ── API Key Loading ──────────────────────────────────────────


def _get_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "")
    if key:
        return key
    try:
        from app.services.local_config import OPENAI_API_KEY

        if OPENAI_API_KEY:
            return OPENAI_API_KEY
    except (ImportError, Exception):
        pass
    for base in [Path(__file__).resolve().parents[3], Path.cwd()]:
        for fname in [".api_key", ".env"]:
            fpath = base / fname
            try:
                content = fpath.read_text().strip()
                if fname == ".api_key":
                    return content
                for line in content.split("\n"):
                    if line.startswith("OPENAI_API_KEY="):
                        return line.split("=", 1)[1].strip().strip("'\"")
            except Exception:
                pass
    return ""


async def _llm_call(system: str, user: str):
    api_key = _get_api_key()
    if not api_key:
        return None
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)
        resp = await client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
            max_completion_tokens=2048,
        )
        return {"text": resp.choices[0].message.content}
    except Exception as e:
        return {"llm_error": str(e)}


# ── Model Registry ───────────────────────────────────────────


@router.get("/registry")
async def get_registry():
    from app.services.model_registry import get_governance_summary, get_model_registry

    return {
        "summary": get_governance_summary(),
        "models": [m.model_dump() for m in get_model_registry()],
    }


@router.get("/registry/{model_id}")
async def get_model_detail(model_id: str):
    from app.services.model_registry import get_model_by_id

    model = get_model_by_id(model_id)
    if model is None:
        return {"error": "Model not found"}
    return model.model_dump()


# ── 1. Document Intelligence ─────────────────────────────────


@router.post("/document-intelligence/extract")
async def demo_document_extract(body: dict):
    text = body.get("text", "")
    if not text:
        return {"error": "Provide 'text' field"}

    if _get_api_key():
        result = await _llm_call(
            "You are a financial document analyst for Morgan Stanley WM. Extract ALL data as JSON: "
            "fund_name, ticker, asset_class, expense_ratio_pct, risk_level, aum_millions, benchmark, "
            "returns, risk_metrics, top_holdings, confidence_score. Only extract what's stated. Nulls for missing.",
            f"Document:\n{text[:8000]}",
        )
        if result and "llm_error" not in result:
            return {
                "model": "WM Document Intelligence v1.0.0",
                "mode": "llm_extraction",
                "powered_by": "GPT-5.2",
                "extraction": result,
            }

    # Rule-based fallback
    fund_name = None
    match = re.search(r"(?:The\s+)?([A-Z][A-Za-z\s&]+(?:Fund|Trust|ETF|Portfolio))", text)
    if match:
        fund_name = match.group(1).strip()

    ticker = None
    match = re.search(r"\(([A-Z]{3,5}X?)\)", text)
    if match:
        ticker = match.group(1)

    expense_ratio = None
    match = re.search(r"expense ratio[:\s]+of\s+([\d.]+)%", text, re.I)
    if match:
        expense_ratio = float(match.group(1))

    holdings = [
        {"ticker": h.group(1), "weight_pct": float(h.group(2))}
        for h in re.finditer(r"([A-Z]{2,5})\s*\(([\d.]+)%\)", text)
    ]

    return {
        "model": "WM Document Intelligence v1.0.0",
        "mode": "rule_based",
        "extraction": {
            "fund_name": fund_name or "Not detected",
            "ticker": ticker,
            "expense_ratio_pct": expense_ratio,
            "top_holdings": holdings or None,
        },
    }


# ── 2. Meeting Summarizer ────────────────────────────────────


@router.post("/meeting-summarizer/summarize")
async def demo_meeting_summarize(body: dict):
    transcript = body.get("transcript", "")
    if not transcript:
        return {"error": "Provide 'transcript' field"}

    if _get_api_key():
        result = await _llm_call(
            "You are a meeting summarization assistant for Morgan Stanley WM. Return JSON: "
            "summary, key_discussion_points, action_items [{description, owner, priority}], "
            "compliance_flags, participants, confidence_score.",
            f"Transcript:\n{transcript[:6000]}",
        )
        if result and "llm_error" not in result:
            return {
                "model": "Meeting Summarizer v1.3.0",
                "mode": "llm_summarization",
                "powered_by": "GPT-5.2",
                "analysis": result,
            }

    lines = [line.strip() for line in transcript.strip().split("\n") if line.strip()]
    speakers: set[str] = set()
    topics: list[str] = []
    for line in lines:
        match = re.match(r"^([\w\s]+):", line)
        if match:
            speakers.add(match.group(1).strip())
        for topic, pattern in [
            ("portfolio review", r"portfolio|allocation"),
            ("retirement", r"retire|401k|ira"),
            ("risk", r"risk|concern"),
            ("estate", r"529|trust|estate"),
        ]:
            if re.search(pattern, line.lower()) and topic not in topics:
                topics.append(topic)

    return {
        "model": "Meeting Summarizer v1.3.0",
        "mode": "rule_based",
        "analysis": {
            "summary": f"Meeting covered: {', '.join(topics) or 'general discussion'}. {len(speakers)} participants.",
            "participants": sorted(speakers),
            "topics": topics,
        },
    }


# ── 3. Portfolio Risk Narrator ───────────────────────────────


@router.post("/portfolio-risk-narrator/generate")
async def demo_risk_narrative(body: dict):
    raw = body.get("portfolio", "")
    if not raw:
        return {"error": "Provide 'portfolio' field (JSON)"}

    # Validate JSON before calling LLM
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(data, dict):
            return {"error": "Invalid JSON: expected an object"}
    except (json.JSONDecodeError, TypeError):
        return {"error": "Invalid JSON: could not parse portfolio data"}

    portfolio_str = json.dumps(data)

    if _get_api_key():
        result = await _llm_call(
            "You are a portfolio risk analyst at Morgan Stanley WM. Generate professional risk commentary "
            "as JSON: executive_summary, performance_commentary, risk_assessment, action_recommendations, "
            "confidence_score. ONLY cite numbers from the data.",
            f"Portfolio:\n{portfolio_str}",
        )
        if result and "llm_error" not in result:
            return {
                "model": "Portfolio Risk Narrator v1.0.0",
                "mode": "llm_narrative",
                "powered_by": "GPT-5.2",
                "narrative": result,
            }

    return {
        "model": "Portfolio Risk Narrator v1.0.0",
        "mode": "rule_based",
        "narrative": {
            "executive_summary": (
                f"Portfolio for {data.get('client_name', 'Client')} "
                f"valued at ${data.get('total_value', 0):,.0f}. "
                f"YTD return {data.get('ytd_return_pct', 0)}%."
            )
        },
    }


# ── 4. Regulatory Change Detector ────────────────────────────


@router.post("/regulatory-change-detector/analyze")
async def demo_regulatory_analyze(body: dict):
    text = body.get("text", "")
    if not text:
        return {"error": "Provide 'text' field"}

    if _get_api_key():
        result = await _llm_call(
            "You are a regulatory change analyst for Morgan Stanley WM. Return JSON: "
            "regulation_title, regulator, impact_level, summary, affected_areas, "
            "required_actions, genai_implications, confidence_score.",
            f"Regulatory Document:\n{text[:8000]}",
        )
        if result and "llm_error" not in result:
            return {
                "model": "Regulatory Change Detector v1.0.0",
                "mode": "llm_analysis",
                "powered_by": "GPT-5.2",
                "analysis": result,
            }

    regulator = "Unknown"
    for reg, pat in [("SEC", r"\bSEC\b"), ("FINRA", r"\bFINRA\b"), ("OCC", r"\bOCC\b")]:
        if re.search(pat, text):
            regulator = reg
            break
    return {
        "model": "Regulatory Change Detector v1.0.0",
        "mode": "rule_based",
        "analysis": {
            "regulator": regulator,
            "impact_level": "high" if "must" in text.lower() else "medium",
        },
    }


# ── 5. Compliance Checker (fully functional, no API key) ─────


@router.post("/compliance-checker/check")
async def demo_compliance_check(body: dict):
    text = body.get("text", "")
    if not text:
        return {"error": "Provide 'text' field"}

    text_lower = text.lower()
    violations: list[dict] = []

    # Disclaimer phrases that negate promissory language
    disclaimer_ctx = [
        "not guarantee", "no guarantee", "does not guarantee",
        "cannot guarantee", "past performance",
    ]

    for pattern, word in [
        (r"\bguarantee[ds]?\b", "guaranteed"),
        (r"\brisk[\s-]?free\b", "risk-free"),
        (r"\bcan'?t lose\b", "can't lose"),
        (r"\bsure thing\b", "sure thing"),
        (r"\bno risk\b", "no risk"),
    ]:
        match = re.search(pattern, text_lower)
        if match:
            # Skip "guarantee" when it appears in disclaimer context
            if word == "guaranteed":
                ctx_start = max(0, match.start() - 25)
                ctx = text_lower[ctx_start : match.end() + 5]
                if any(d in ctx for d in disclaimer_ctx):
                    continue
            violations.append(
                {
                    "type": "promissory_language",
                    "severity": "high",
                    "evidence": text[max(0, match.start() - 30) : match.end() + 30].strip(),
                    "regulation": "FINRA Rule 2210(d)(1)(B)",
                    "fix": f"Remove '{word}'",
                }
            )

    has_perf = bool(re.search(r"\d+\.?\d*%\s*(return|performance|gain|annual)", text_lower))
    has_disc = any(p in text_lower for p in ["past performance", "no guarantee", "may lose value"])
    if has_perf and not has_disc:
        violations.append(
            {
                "type": "missing_disclosure",
                "severity": "high",
                "evidence": "Performance data without disclaimer",
                "regulation": "SEC Marketing Rule 206(4)-1",
                "fix": "Add past performance disclaimer",
            }
        )

    if re.search(r"\b\d{3}-\d{2}-\d{4}\b", text):
        violations.append(
            {
                "type": "pii_detected",
                "severity": "high",
                "evidence": "[SSN REDACTED]",
                "regulation": "Reg S-P",
                "fix": "Remove SSN",
            }
        )

    high = sum(1 for v in violations if v["severity"] == "high")
    decision = "rejected" if high >= 2 else "requires_changes" if violations else "approved"
    return {
        "model": "Compliance Checker v1.0.0",
        "mode": "fully_functional",
        "decision": decision,
        "violations": violations,
        "risk_score": min(1.0, len(violations) * 0.2 + high * 0.3),
    }
