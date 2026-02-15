"""
Compliance control mapping – structured tables that map every risk to a Control Tower control.

This module is the single source of truth for:
  - OWASP LLM Top 10 (2025) → Control Tower controls
  - OWASP Agentic Top 10 (2026) → Control Tower controls
  - NIST AI 600-1 GenAI Profile → Control Tower controls
  - MITRE ATLAS techniques → Control Tower detections
  - SR 11-7 / OCC principles → Control Tower implementation
  - FINRA GenAI expectations → Control Tower implementation

This is the artifact an ED or regulator reviews to confirm coverage.
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# OWASP LLM Top 10 (2025) → Control Tower Controls
# ─────────────────────────────────────────────────────────────────────────────
OWASP_LLM_TOP10_2025: list[dict] = [
    {
        "id": "LLM01",
        "name": "Prompt Injection",
        "description": "Adversarial prompts that alter LLM behavior or bypass instructions.",
        "controls": [
            "Cascade guardrail: Stage 1 regex + Stage 2 ML classifier (guardrails.py)",
            "promptfoo red-team suite with 20+ injection patterns (redteam_config.yaml)",
            "PyRIT scenario: financial_advisor_injection.py with 10 attack vectors",
            "OPA policy: agent_controls.rego blocks dangerous tool patterns",
            "Input sanitization + prompt template hashing (FINRA version tracking)",
        ],
        "eval_tools": ["promptfoo", "PyRIT", "garak (promptinject probes)"],
        "mitre_atlas": "AML.T0051",
    },
    {
        "id": "LLM02",
        "name": "Insecure Output Handling",
        "description": "Trusting LLM output without validation in downstream systems.",
        "controls": [
            "Output guardrails: PII scan, toxicity check, format validation",
            "Human-in-the-loop enforced for client-facing outputs (policy gate)",
            "Output logged + hashed as evidence artifact (FINRA requirement)",
        ],
        "eval_tools": ["promptfoo (output assertion tests)", "garak (xss probes)"],
        "mitre_atlas": "AML.T0048",
    },
    {
        "id": "LLM04",
        "name": "Output Handling (Model DoS/Resource)",
        "description": "Excessive resource consumption or denial-of-service via prompts.",
        "controls": [
            "Token budget enforcement per request",
            "Rate limiting at API gateway",
            "Cost tracking per evaluation run",
            "Circuit breaker in agent workflow (Temporal retry policy)",
        ],
        "eval_tools": ["promptfoo (cost threshold assertions)"],
        "mitre_atlas": "AML.T0029",
    },
    {
        "id": "LLM06",
        "name": "Sensitive Information Disclosure",
        "description": "LLM reveals PII, credentials, or confidential data.",
        "controls": [
            "PII redaction on outputs (pii_redaction.py with Presidio integration)",
            "OPA data_classification.rego: destination allowlist per data class",
            "Guardrail Stage 1 PII regex scan on all outputs",
            "Retrieval entitlement simulation in RAG pipeline",
            "Prompt/output logging with automatic PII redaction (FINRA)",
        ],
        "eval_tools": ["promptfoo (PII leak tests)", "garak (leakreplay probes)", "PyRIT"],
        "mitre_atlas": "AML.T0024",
    },
    {
        "id": "LLM07",
        "name": "Excessive Agency",
        "description": "LLM with too many capabilities, permissions, or autonomy.",
        "controls": [
            "OPA tool_permissions.rego: role-based tool allowlists",
            "OPA agent_controls.rego: per-turn tool call limits, sandboxed execution",
            "Human approval gate for high-risk tool calls (e.g., save_to_crm)",
            "Agent registry with signed configs + kill switch (ASI10 aligned)",
            "Least-privilege: scoped credentials per tool",
        ],
        "eval_tools": ["promptfoo (excessive-agency plugin)", "PyRIT"],
        "mitre_atlas": "AML.T0040",
    },
    {
        "id": "LLM08",
        "name": "Data and Model Poisoning",
        "description": "Compromised training data or retrieval corpus.",
        "controls": [
            "AIBOM (CycloneDX) for model supply chain transparency",
            "Dataset provenance tracking (Dataset entity with SHA-256 hash)",
            "Retrieval corpus versioning + signing",
            "Monitoring: corpus change triggers recertification",
        ],
        "eval_tools": ["garak (encoding-based probes)"],
        "mitre_atlas": "AML.T0020",
    },
    {
        "id": "LLM09",
        "name": "Misinformation / Hallucination",
        "description": "LLM generates factually incorrect or unsupported claims.",
        "controls": [
            "RAG groundedness evaluation (TruLens RAG Triad metrics)",
            "Mandatory citation enforcement for Q&A use cases",
            "Golden test set regression (daily via promptfoo)",
            "Canary prompts in monitoring plan for drift detection",
        ],
        "eval_tools": ["promptfoo (llm-rubric)", "garak (snowball probes)"],
        "mitre_atlas": "AML.T0048",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# OWASP Agentic Top 10 (2026) → Control Tower Controls
# ─────────────────────────────────────────────────────────────────────────────
OWASP_AGENTIC_TOP10_2026: list[dict] = [
    {
        "id": "ASI01",
        "name": "Agent Goal Hijack",
        "controls": [
            "System prompt hardening + immutable instruction prefix",
            "Goal drift evaluation in agentic_safety test suite",
            "Adversarial instruction tests via PyRIT scenarios",
        ],
    },
    {
        "id": "ASI02",
        "name": "Tool Misuse",
        "controls": [
            "OPA tool_permissions.rego: strict allowlist per role",
            "Argument schema validation for each tool",
            "Human approval gate for destructive/write operations",
        ],
    },
    {
        "id": "ASI03",
        "name": "Identity / Privilege Abuse",
        "controls": [
            "Scoped credentials per tool (no shared service accounts)",
            "Per-tool token issuance via Keycloak service accounts",
            "Least-privilege enforcement in OPA policy",
        ],
    },
    {
        "id": "ASI05",
        "name": "Unexpected Code Execution (RCE)",
        "controls": [
            "OPA agent_controls.rego blocks dangerous patterns (eval, exec, subprocess)",
            "Sandboxed tool execution (Docker container isolation)",
            "No dynamic code generation without explicit approval",
        ],
    },
    {
        "id": "ASI06",
        "name": "Memory / Context Poisoning",
        "controls": [
            "Memory write provenance tracking (source + timestamp required)",
            "TTL enforcement on memory entries",
            "Memory write count limits (OPA: max 10 per turn)",
            "Immutable memory audit trail in evidence store",
        ],
    },
    {
        "id": "ASI08",
        "name": "Cascading Failures",
        "controls": [
            "Temporal workflow retry policies with bounded attempts (max 3)",
            "Circuit breaker pattern in tool invocations",
            "Per-turn tool call limits (OPA: max 5)",
            "Fallback policies with graceful degradation",
        ],
    },
    {
        "id": "ASI10",
        "name": "Rogue Agents",
        "controls": [
            "Agent registry: all agents must be registered with signed configs",
            "Kill switch: OPA checks execution_context.kill_switch_active",
            "Agent behavior monitoring with anomaly detection thresholds",
            "Mandatory human-in-the-loop for new agent capabilities",
        ],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# NIST AI 600-1 GenAI Profile → Control Tower Implementation
# ─────────────────────────────────────────────────────────────────────────────
NIST_GENAI_PROFILE: dict[str, dict] = {
    "governance": {
        "nist_requirement": "Establish and maintain governance structures for GenAI systems.",
        "ct_implementation": [
            "RBAC via Keycloak (6 roles: admin, MRO, analyst, BLH, auditor, developer)",
            "OPA approval gates enforce risk-tier-based approval chains",
            "Use case intake with automated risk assessment and committee routing",
            "ISO 42001 PDCA lifecycle tracking on every use case",
        ],
    },
    "content_provenance": {
        "nist_requirement": "Track and verify the origin and chain of custody of AI-generated content.",
        "ct_implementation": [
            "Mandatory citations in RAG Q&A (enforced by eval tests)",
            "Dataset provenance with SHA-256 hashing and source tracking",
            "AIBOM (CycloneDX) for model supply chain transparency",
            "Evidence artifacts are content-addressed with hash chains",
        ],
    },
    "pre_deployment_testing": {
        "nist_requirement": "Conduct comprehensive testing before deploying GenAI systems.",
        "ct_implementation": [
            "3-layer evaluation: promptfoo (quality/red-team), PyRIT (security), garak (vulnerability)",
            "Risk-tier-based test suite requirements (critical: 9 suites, minimal: 1)",
            "RAG groundedness evaluation (faithfulness, relevance, context precision)",
            "Operational controls verification (logging, versioning, HITL, PII redaction)",
            "CI pipeline runs evaluations on every PR (eval.yml workflow)",
        ],
    },
    "incident_disclosure": {
        "nist_requirement": "Disclose and respond to AI system incidents.",
        "ct_implementation": [
            "Finding → Issue escalation workflow with severity-based routing",
            "NIST incident_disclosure JSONB field on every use case",
            "Monitoring alerts with configurable routing (Slack, email, PagerDuty)",
            "Immutable audit event stream for forensic investigation",
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# SR 11-7 / OCC Model Risk Principles → Control Tower Implementation
# ─────────────────────────────────────────────────────────────────────────────
SR_11_7_MAPPING: dict[str, dict] = {
    "model_definition": {
        "principle": "A model is a quantitative method that processes input data to produce quantitative estimates.",
        "ct_implementation": [
            "Model entity captures type (statistical/ML/LLM/multimodal), purpose, inputs/outputs, limitations",
            "GenAI use cases tracked separately with explicit model linkage",
            "Tool/EUC inventory for non-model quantitative tools",
        ],
    },
    "effective_challenge": {
        "principle": "Critical analysis by objective, informed parties that can identify model limitations.",
        "ct_implementation": [
            "Certification pipeline: intake → risk assessment → testing → approval → monitoring",
            "Temporal workflow enforces every step with retry and audit",
            "Three independent evaluation layers (promptfoo + PyRIT + garak)",
            "Policy engine (OPA) provides objective, code-based challenge",
            "Evidence pack documents the complete effective challenge record",
        ],
    },
    "governance": {
        "principle": "Board and senior management oversight of model risk.",
        "ct_implementation": [
            "Risk-tier-based committee paths (Model Control → WM MRC → Enterprise RC → Board RC)",
            "Committee report endpoint with pipeline funnel and findings aging",
            "Approval records with tamper-evident hashing (SHA-256)",
            "Audit event stream for complete governance traceability",
        ],
    },
    "ongoing_monitoring": {
        "principle": "Continuous monitoring to identify issues promptly.",
        "ct_implementation": [
            "Monitoring plans with configurable cadence (real-time to quarterly)",
            "Canary prompts for regression detection",
            "Threshold-based drift alerting",
            "Automatic recertification triggers (model version change, corpus change, etc.)",
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# FINRA GenAI Control Expectations → Control Tower Implementation
# ─────────────────────────────────────────────────────────────────────────────
FINRA_GENAI_MAPPING: dict[str, dict] = {
    "prompt_output_logging": {
        "expectation": "Firms should capture prompt and output logs for GenAI systems.",
        "ct_implementation": [
            "EvaluationResult captures input_prompt, actual_output, context_used",
            "PII redaction applied before storage (pii_redaction.py)",
            "Evidence artifacts store prompt/output logs as content-addressed files",
            "OpenTelemetry traces capture full request/response lifecycle",
        ],
    },
    "model_version_tracking": {
        "expectation": "Track model version used for every interaction.",
        "ct_implementation": [
            "EvaluationRun records model_provider + model_version + prompt_template_hash",
            "Model entity maintains version history",
            "Monitoring plan triggers recertification on version change",
        ],
    },
    "monitoring_emerging_features": {
        "expectation": "Monitor emerging features like agentic AI.",
        "ct_implementation": [
            "OWASP Agentic Top 10 2026 explicitly covered in agent_controls.rego",
            "Agentic safety evaluation suite in test requirements",
            "Agent registry with kill switch and behavior monitoring",
            "Tool permission controls with per-turn limits",
        ],
    },
}


def get_full_compliance_matrix() -> dict:
    """Return the complete compliance mapping for reporting."""
    return {
        "owasp_llm_top10_2025": OWASP_LLM_TOP10_2025,
        "owasp_agentic_top10_2026": OWASP_AGENTIC_TOP10_2026,
        "nist_ai_600_1": NIST_GENAI_PROFILE,
        "sr_11_7": SR_11_7_MAPPING,
        "finra_genai": FINRA_GENAI_MAPPING,
    }
