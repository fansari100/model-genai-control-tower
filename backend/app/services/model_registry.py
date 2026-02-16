"""
Model Registry — complete inventory of all 5 GenAI vendor models.

Each model entry contains:
  - Vendor details and methodology description
  - Risk assessment (data classification, architecture flags)
  - Certification status and history
  - Compliance framework mapping
  - Monitoring configuration
  - Evaluation results summary
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ModelStatus(str, Enum):
    DRAFT = "draft"
    INTAKE = "intake"
    TESTING = "testing"
    CERTIFIED = "certified"
    CONDITIONAL = "conditional"
    MONITORING = "monitoring"
    RECERTIFICATION = "recertification"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class RiskRating(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvalResult(BaseModel):
    eval_type: str
    total_tests: int
    passed: int
    failed: int
    pass_rate: float
    date: str
    details: dict[str, Any] = {}


class ComplianceMapping(BaseModel):
    sr_11_7: list[str] = []
    nist_600_1: list[str] = []
    owasp_llm_2025: list[str] = []
    owasp_agentic_2026: list[str] = []
    finra: list[str] = []


class MonitoringConfig(BaseModel):
    cadence: str = "daily"
    canary_prompts: list[dict] = []
    thresholds: dict[str, float] = {}
    last_execution: str | None = None
    drift_detected: bool = False


class GovernedModel(BaseModel):
    """A GenAI model under governance."""

    # Identity
    id: str
    name: str
    version: str
    vendor: str
    description: str
    methodology: str

    # Classification
    model_type: str  # extraction, summarization, generation, classification, analysis
    risk_rating: RiskRating
    status: ModelStatus

    # Architecture
    base_model: str  # e.g., "gpt-5.2", "claude-sonnet-4"
    uses_rag: bool = False
    uses_structured_output: bool = True
    client_facing: bool = False
    handles_pii: bool = False
    data_classification: str = "internal"

    # Governance
    owner: str
    business_unit: str = "Wealth Management"
    certification_date: str | None = None
    next_recertification: str | None = None
    committee_path: str = "WM Model Risk Committee"

    # Compliance
    compliance: ComplianceMapping = ComplianceMapping()

    # Evaluation
    eval_results: list[EvalResult] = []
    overall_pass_rate: float | None = None

    # Monitoring
    monitoring: MonitoringConfig = MonitoringConfig()

    # Findings
    open_findings: int = 0
    total_findings: int = 0


# ── Pre-configured registry of all 5 models ─────────────────────────────────

MODEL_REGISTRY: list[GovernedModel] = [
    GovernedModel(
        id="WM-DOC-INT-001",
        name="WM Document Intelligence",
        version="1.0.0",
        vendor="Internal (WM AI Platform)",
        description="Extracts structured financial data from unstructured documents (prospectuses, fund fact sheets, investment policy statements)",
        methodology="RAG pipeline with ChromaDB vector store + GPT-4o structured output (Pydantic) + business rules validation",
        model_type="extraction",
        risk_rating=RiskRating.HIGH,
        status=ModelStatus.CERTIFIED,
        base_model="gpt-5.2",
        uses_rag=True,
        handles_pii=False,
        data_classification="confidential",
        owner="AI Platform Team",
        certification_date="2026-01-15",
        next_recertification="2026-07-15",
        compliance=ComplianceMapping(
            sr_11_7=["Model Definition", "Effective Challenge", "Ongoing Monitoring"],
            nist_600_1=["Content Provenance", "Pre-deployment Testing"],
            owasp_llm_2025=["LLM01 Prompt Injection", "LLM09 Misinformation"],
            finra=["Prompt/output logging", "Model version tracking"],
        ),
        eval_results=[
            EvalResult(eval_type="quality_correctness", total_tests=25, passed=24, failed=1, pass_rate=0.96, date="2026-01-10"),
            EvalResult(eval_type="safety_security", total_tests=30, passed=29, failed=1, pass_rate=0.967, date="2026-01-12"),
            EvalResult(eval_type="rag_groundedness", total_tests=20, passed=19, failed=1, pass_rate=0.95, date="2026-01-11"),
        ],
        overall_pass_rate=0.96,
        monitoring=MonitoringConfig(
            cadence="daily",
            canary_prompts=[{"prompt": "Extract fund name and expense ratio from this prospectus", "expected_contains": "fund_name"}],
            thresholds={"accuracy_min": 0.90, "latency_p99_ms": 5000},
        ),
        open_findings=1,
        total_findings=3,
    ),
    GovernedModel(
        id="WM-MTG-SUM-001",
        name="Client Meeting Summarizer",
        version="1.3.0",
        vendor="Internal (WM Technology)",
        description="Summarizes advisor-client meeting transcripts into structured notes, action items, compliance flags, and draft follow-up emails",
        methodology="GPT-4o structured output with PII detection (Presidio + regex), compliance rule engine, human-in-the-loop email approval",
        model_type="summarization",
        risk_rating=RiskRating.HIGH,
        status=ModelStatus.MONITORING,
        base_model="gpt-5.2",
        client_facing=True,
        handles_pii=True,
        data_classification="pii",
        owner="WM Technology",
        certification_date="2025-11-01",
        next_recertification="2026-05-01",
        compliance=ComplianceMapping(
            sr_11_7=["Model Definition", "Effective Challenge", "Governance", "Ongoing Monitoring"],
            nist_600_1=["Governance", "Content Provenance", "Pre-deployment Testing", "Incident Disclosure"],
            owasp_llm_2025=["LLM01 Prompt Injection", "LLM06 Sensitive Disclosure", "LLM09 Misinformation"],
            finra=["Prompt/output logging", "Model version tracking", "PII redaction"],
        ),
        eval_results=[
            EvalResult(eval_type="quality_correctness", total_tests=30, passed=28, failed=2, pass_rate=0.933, date="2025-10-20"),
            EvalResult(eval_type="safety_security", total_tests=40, passed=38, failed=2, pass_rate=0.95, date="2025-10-22"),
            EvalResult(eval_type="pii_redaction", total_tests=15, passed=15, failed=0, pass_rate=1.0, date="2025-10-21"),
        ],
        overall_pass_rate=0.95,
        monitoring=MonitoringConfig(cadence="daily", thresholds={"faithfulness_min": 0.85, "pii_leak_max": 0.0}),
        open_findings=2,
        total_findings=5,
    ),
    GovernedModel(
        id="WM-RSK-NAR-001",
        name="Portfolio Risk Narrator",
        version="1.0.0",
        vendor="Internal (Risk Analytics)",
        description="Generates natural-language risk commentary from structured portfolio analytics for client reports and committee presentations",
        methodology="Data-to-text generation with GPT-4o structured output + fact-checking layer (verifies all cited numbers against source data)",
        model_type="generation",
        risk_rating=RiskRating.MEDIUM,
        status=ModelStatus.CERTIFIED,
        base_model="gpt-5.2",
        client_facing=True,
        handles_pii=False,
        data_classification="confidential",
        owner="Risk Analytics",
        certification_date="2026-02-01",
        next_recertification="2026-08-01",
        compliance=ComplianceMapping(
            sr_11_7=["Model Definition", "Effective Challenge"],
            nist_600_1=["Content Provenance", "Pre-deployment Testing"],
            owasp_llm_2025=["LLM09 Misinformation"],
            finra=["Model version tracking"],
        ),
        eval_results=[
            EvalResult(eval_type="quality_correctness", total_tests=20, passed=19, failed=1, pass_rate=0.95, date="2026-01-28"),
            EvalResult(eval_type="fact_verification", total_tests=50, passed=48, failed=2, pass_rate=0.96, date="2026-01-29",
                       details={"numbers_verified": 48, "numbers_unverified": 2}),
        ],
        overall_pass_rate=0.955,
        monitoring=MonitoringConfig(cadence="weekly", thresholds={"fact_accuracy_min": 0.95}),
        open_findings=0,
        total_findings=2,
    ),
    GovernedModel(
        id="WM-REG-DET-001",
        name="Regulatory Change Detector",
        version="1.0.0",
        vendor="Internal (Compliance)",
        description="Monitors regulatory updates (SEC/FINRA/OCC) and identifies changes impacting WM operations with semantic similarity matching",
        methodology="Semantic embedding (text-embedding-3-large) + ChromaDB similarity search against WM control catalog + GPT-4o impact analysis",
        model_type="analysis",
        risk_rating=RiskRating.MEDIUM,
        status=ModelStatus.TESTING,
        base_model="gpt-5.2",
        uses_rag=True,
        handles_pii=False,
        data_classification="internal",
        owner="Compliance",
        compliance=ComplianceMapping(
            sr_11_7=["Model Definition", "Effective Challenge"],
            nist_600_1=["Governance", "Pre-deployment Testing"],
            owasp_llm_2025=["LLM01 Prompt Injection", "LLM09 Misinformation"],
        ),
        eval_results=[
            EvalResult(eval_type="quality_correctness", total_tests=15, passed=14, failed=1, pass_rate=0.933, date="2026-02-10"),
        ],
        overall_pass_rate=0.933,
        open_findings=1,
        total_findings=1,
    ),
    GovernedModel(
        id="WM-CMP-CHK-001",
        name="Client Communication Compliance Checker",
        version="1.0.0",
        vendor="Internal (Compliance)",
        description="Pre-send compliance screening for advisor communications — checks for misleading claims, missing disclosures, PII, suitability violations",
        methodology="GPT-4o classification with structured output + deterministic rule-based checks (promissory language regex, PII patterns) + FINRA 2210 rule engine",
        model_type="classification",
        risk_rating=RiskRating.HIGH,
        status=ModelStatus.CERTIFIED,
        base_model="gpt-5.2",
        client_facing=False,
        handles_pii=True,
        data_classification="confidential",
        owner="Compliance",
        certification_date="2026-02-05",
        next_recertification="2026-08-05",
        compliance=ComplianceMapping(
            sr_11_7=["Model Definition", "Effective Challenge", "Ongoing Monitoring"],
            nist_600_1=["Governance", "Pre-deployment Testing"],
            owasp_llm_2025=["LLM01 Prompt Injection", "LLM06 Sensitive Disclosure"],
            finra=["FINRA 2210 (Communications)", "FINRA 2111 (Suitability)", "Prompt/output logging"],
        ),
        eval_results=[
            EvalResult(eval_type="quality_correctness", total_tests=40, passed=39, failed=1, pass_rate=0.975, date="2026-02-03"),
            EvalResult(eval_type="safety_security", total_tests=25, passed=24, failed=1, pass_rate=0.96, date="2026-02-04"),
            EvalResult(eval_type="false_positive_rate", total_tests=30, passed=28, failed=2, pass_rate=0.933, date="2026-02-04",
                       details={"false_positives": 2, "false_negatives": 0}),
        ],
        overall_pass_rate=0.96,
        monitoring=MonitoringConfig(cadence="daily", thresholds={"detection_rate_min": 0.95, "false_positive_max": 0.05}),
        open_findings=1,
        total_findings=3,
    ),
]


def get_model_registry() -> list[GovernedModel]:
    return MODEL_REGISTRY


def get_model_by_id(model_id: str) -> GovernedModel | None:
    return next((m for m in MODEL_REGISTRY if m.id == model_id), None)


def get_governance_summary() -> dict:
    """Dashboard summary of all governed models."""
    models = MODEL_REGISTRY
    return {
        "total_models": len(models),
        "by_status": {s.value: sum(1 for m in models if m.status == s) for s in ModelStatus if any(m.status == s for m in models)},
        "by_risk": {r.value: sum(1 for m in models if m.risk_rating == r) for r in RiskRating if any(m.risk_rating == r for m in models)},
        "avg_pass_rate": sum(m.overall_pass_rate or 0 for m in models) / len(models),
        "total_open_findings": sum(m.open_findings for m in models),
        "total_eval_runs": sum(len(m.eval_results) for m in models),
        "certified_count": sum(1 for m in models if m.status in (ModelStatus.CERTIFIED, ModelStatus.MONITORING)),
    }
