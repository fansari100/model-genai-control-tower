"""
Risk rating engine – computes initial risk score and classification for GenAI use cases.

Implements a weighted factor model aligned with:
- SR 11-7 / OCC model risk tiers
- NIST AI 600-1 GenAI Profile considerations
- OWASP LLM Top 10 (2025) + Agentic Top 10 (2026)
- FINRA GenAI control expectations
"""

from __future__ import annotations

from app.models.genai_use_case import DataClassification, RiskRating, UseCaseCategory

# ── Risk Factor Weights ──────────────────────────────────────────────────────

DATA_CLASS_WEIGHTS: dict[DataClassification, int] = {
    DataClassification.PUBLIC: 0,
    DataClassification.INTERNAL: 10,
    DataClassification.CONFIDENTIAL: 25,
    DataClassification.PII: 40,
    DataClassification.RESTRICTED: 50,
}

CATEGORY_WEIGHTS: dict[UseCaseCategory, int] = {
    UseCaseCategory.AGENT_WORKFLOW: 25,
    UseCaseCategory.CONTENT_GENERATION: 15,
    UseCaseCategory.CODE_GENERATION: 20,
    UseCaseCategory.SUMMARIZATION: 10,
    UseCaseCategory.RAG_QA: 10,
    UseCaseCategory.DATA_EXTRACTION: 15,
    UseCaseCategory.CLASSIFICATION: 5,
    UseCaseCategory.TRANSLATION: 5,
    UseCaseCategory.OTHER: 10,
}

BOOL_WEIGHTS: dict[str, int] = {
    "handles_pii": 30,
    "client_facing": 35,
    "uses_agents": 30,
    "uses_tools": 20,
    "uses_memory": 15,
    "uses_rag": 10,
}

# ── Score → Rating Thresholds ────────────────────────────────────────────────

RATING_THRESHOLDS: list[tuple[int, RiskRating]] = [
    (150, RiskRating.CRITICAL),
    (100, RiskRating.HIGH),
    (50, RiskRating.MEDIUM),
    (20, RiskRating.LOW),
    (0, RiskRating.MINIMAL),
]

# ── Test Suite Requirements per Rating ───────────────────────────────────────

TEST_SUITE_MAP: dict[RiskRating, list[str]] = {
    RiskRating.CRITICAL: [
        "quality_correctness",
        "rag_groundedness",
        "safety_security",
        "red_team_promptfoo",
        "red_team_pyrit",
        "vulnerability_garak",
        "agentic_safety",
        "operational_controls",
        "regression",
    ],
    RiskRating.HIGH: [
        "quality_correctness",
        "rag_groundedness",
        "safety_security",
        "red_team_promptfoo",
        "vulnerability_garak",
        "operational_controls",
        "regression",
    ],
    RiskRating.MEDIUM: [
        "quality_correctness",
        "safety_security",
        "red_team_promptfoo",
        "operational_controls",
    ],
    RiskRating.LOW: [
        "quality_correctness",
        "operational_controls",
    ],
    RiskRating.MINIMAL: [
        "quality_correctness",
    ],
}

# ── Approval Requirements per Rating ─────────────────────────────────────────

APPROVAL_MAP: dict[RiskRating, list[str]] = {
    RiskRating.CRITICAL: [
        "model_risk_officer",
        "chief_risk_officer",
        "technology_risk_committee",
        "business_line_head",
    ],
    RiskRating.HIGH: [
        "model_risk_officer",
        "technology_risk_committee",
        "business_line_head",
    ],
    RiskRating.MEDIUM: [
        "model_risk_officer",
        "business_line_head",
    ],
    RiskRating.LOW: [
        "model_control_analyst",
    ],
    RiskRating.MINIMAL: [
        "model_control_analyst",
    ],
}

# ── Committee Path per Rating ────────────────────────────────────────────────

COMMITTEE_MAP: dict[RiskRating, str] = {
    RiskRating.CRITICAL: "WM Model Risk Committee → Enterprise Risk Committee → Board Risk Committee",
    RiskRating.HIGH: "WM Model Risk Committee → Enterprise Risk Committee",
    RiskRating.MEDIUM: "WM Model Risk Committee",
    RiskRating.LOW: "Model Control Review",
    RiskRating.MINIMAL: "Model Control Review",
}

# ── OWASP Risk Identification ────────────────────────────────────────────────


def _identify_owasp_llm_risks(
    uses_rag: bool,
    uses_agents: bool,
    uses_tools: bool,
    handles_pii: bool,
    client_facing: bool,
) -> list[str]:
    """Map use case characteristics to OWASP LLM Top 10 (2025) risks."""
    risks: list[str] = ["LLM01_Prompt_Injection"]  # Always applicable

    if uses_rag:
        risks.append("LLM08_Data_Model_Poisoning")
    if handles_pii:
        risks.append("LLM06_Sensitive_Information_Disclosure")
    if uses_agents or uses_tools:
        risks.append("LLM06_Excessive_Agency")
        risks.append("LLM04_Output_Handling")
    if client_facing:
        risks.append("LLM09_Misinformation")
        risks.append("LLM02_Insecure_Output_Handling")

    return sorted(set(risks))


def _identify_owasp_agentic_risks(
    uses_agents: bool,
    uses_tools: bool,
    uses_memory: bool,
) -> list[str]:
    """Map to OWASP Agentic Top 10 (2026) risks."""
    if not uses_agents:
        return []

    risks = [
        "ASI01_Agent_Goal_Hijack",
        "ASI08_Cascading_Failures",
        "ASI10_Rogue_Agents",
    ]

    if uses_tools:
        risks.extend(
            [
                "ASI02_Tool_Misuse",
                "ASI03_Identity_Privilege_Abuse",
                "ASI05_Unexpected_RCE",
            ]
        )
    if uses_memory:
        risks.append("ASI06_Memory_Context_Poisoning")

    return sorted(set(risks))


def _identify_nist_considerations(
    uses_rag: bool,
    client_facing: bool,
    uses_agents: bool,
) -> dict:
    """Map to NIST AI 600-1 GenAI Profile primary considerations."""
    return {
        "governance": {
            "applicable": True,
            "controls": [
                "roles_and_approval_gates",
                "usage_restrictions",
                "human_in_loop_requirements",
            ],
        },
        "content_provenance": {
            "applicable": uses_rag or client_facing,
            "controls": (
                ["citation_chain", "data_lineage", "source_linking"]
                if uses_rag
                else ["output_attribution"]
            ),
        },
        "pre_deployment_testing": {
            "applicable": True,
            "controls": [
                "offline_evals",
                "red_team_assessment",
                "regression_testing",
            ],
        },
        "incident_disclosure": {
            "applicable": True,
            "controls": [
                "issue_escalation",
                "evidence_capture",
                "remediation_tracking",
            ],
        },
    }


def compute_risk_rating(
    data_classification: DataClassification,
    handles_pii: bool,
    client_facing: bool,
    uses_agents: bool,
    uses_tools: bool,
    uses_memory: bool,
    uses_rag: bool,
    category: UseCaseCategory,
) -> dict:
    """
    Compute the complete risk assessment for a GenAI use case.

    Scoring methodology:
      1. Each input factor has a defined weight.
      2. Weights are summed to produce a composite risk score.
      3. Score is mapped to a risk rating via threshold bands.
      4. Rating determines required test suites, approvals, and committee path.

    Returns:
        dict with risk_rating, risk_score, risk_factors, required_test_suites,
        required_approvals, committee_path, nist_considerations, owasp_*_risks.
    """
    factors: list[dict] = []
    total_score: float = 0.0

    # ── Score: data classification ───────────────────────────
    dc_weight = DATA_CLASS_WEIGHTS.get(data_classification, 0)
    total_score += dc_weight
    if dc_weight > 0:
        factors.append(
            {
                "factor": "data_classification",
                "value": data_classification.value,
                "weight": dc_weight,
            }
        )

    # ── Score: category ──────────────────────────────────────
    cat_weight = CATEGORY_WEIGHTS.get(category, 10)
    total_score += cat_weight
    if cat_weight > 0:
        factors.append({"factor": "category", "value": category.value, "weight": cat_weight})

    # ── Score: boolean flags ─────────────────────────────────
    bool_values: dict[str, bool] = {
        "handles_pii": handles_pii,
        "client_facing": client_facing,
        "uses_agents": uses_agents,
        "uses_tools": uses_tools,
        "uses_memory": uses_memory,
        "uses_rag": uses_rag,
    }
    for flag_name, flag_value in bool_values.items():
        if flag_value:
            weight = BOOL_WEIGHTS[flag_name]
            total_score += weight
            factors.append({"factor": flag_name, "value": "true", "weight": weight})

    # ── Determine rating from composite score ────────────────
    rating = RiskRating.MINIMAL
    for threshold, r in RATING_THRESHOLDS:
        if total_score >= threshold:
            rating = r
            break

    # ── Identify applicable risks ────────────────────────────
    owasp_llm = _identify_owasp_llm_risks(
        uses_rag, uses_agents, uses_tools, handles_pii, client_facing
    )
    owasp_agentic = _identify_owasp_agentic_risks(uses_agents, uses_tools, uses_memory)
    nist = _identify_nist_considerations(uses_rag, client_facing, uses_agents)

    # ── Estimated days based on rating ───────────────────────
    days_map: dict[RiskRating, int] = {
        RiskRating.CRITICAL: 30,
        RiskRating.HIGH: 21,
        RiskRating.MEDIUM: 14,
        RiskRating.LOW: 7,
        RiskRating.MINIMAL: 3,
    }

    return {
        "risk_rating": rating,
        "risk_score": total_score,
        "risk_factors": sorted(factors, key=lambda f: f["weight"], reverse=True),
        "required_test_suites": TEST_SUITE_MAP[rating],
        "required_approvals": APPROVAL_MAP[rating],
        "committee_path": COMMITTEE_MAP[rating],
        "nist_considerations": nist,
        "owasp_llm_risks": owasp_llm,
        "owasp_agentic_risks": owasp_agentic,
        "estimated_days": days_map[rating],
    }
