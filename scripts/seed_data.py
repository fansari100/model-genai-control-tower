"""
Seed the Control Tower database with realistic demo data.

Usage: cd backend && python -m scripts.seed_data
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add parent to path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import async_session_factory, engine, Base
from app.models.vendor import Vendor, VendorSecurityPosture
from app.models.model import Model, ModelType, ModelDeployment, ModelStatus, RiskTier
from app.models.tool import Tool, ToolCategory, ToolCriticality, ToolStatus
from app.models.genai_use_case import (
    GenAIUseCase, UseCaseCategory, UseCaseStatus, RiskRating, DataClassification,
    UseCaseModelLink, UseCaseToolLink,
)
from app.models.evaluation import EvaluationRun, EvaluationResult, EvalType, EvalStatus
from app.models.finding import Finding, FindingSeverity, FindingStatus, FindingSource
from app.models.approval import Approval, ApprovalDecision, ApprovalGateType
from app.models.monitoring import MonitoringPlan, MonitoringCadence
from app.models.dataset import Dataset, DatasetType


async def seed() -> None:
    """Seed the database with demo data."""
    print("🌱 Seeding Control Tower database...")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # ── Vendors ──────────────────────────────────────────
        openai = Vendor(
            name="OpenAI",
            legal_entity="OpenAI OpCo LLC",
            contract_id="VENDOR-OAI-2024",
            contact_email="enterprise@openai.com",
            description="Large language model provider – GPT family",
            security_posture=VendorSecurityPosture.APPROVED,
            sla_summary="99.9% uptime SLA, 30-day data retention opt-out",
            data_processing_region="US",
            certifications={"soc2": True, "iso27001": True},
            redteam_due_diligence={
                "threat_model_coverage": "high",
                "eval_rigor": "high",
                "reproducibility": "medium",
                "evidence_quality": "high",
            },
        )
        anthropic = Vendor(
            name="Anthropic",
            legal_entity="Anthropic PBC",
            contract_id="VENDOR-ANT-2025",
            contact_email="sales@anthropic.com",
            description="AI safety company – Claude family",
            security_posture=VendorSecurityPosture.APPROVED,
            sla_summary="99.9% uptime, zero data retention available",
            data_processing_region="US",
            certifications={"soc2": True, "iso27001": True},
        )
        google = Vendor(
            name="Google DeepMind",
            legal_entity="Google LLC",
            contract_id="VENDOR-GOOG-2026",
            contact_email="cloud-ai@google.com",
            description="Gemini family of multimodal models",
            security_posture=VendorSecurityPosture.APPROVED,
            sla_summary="99.95% uptime, configurable data residency",
            data_processing_region="US",
            certifications={"soc2": True, "iso27001": True, "fedramp": True},
        )
        session.add_all([openai, anthropic, google])
        await session.flush()

        # ── Models ───────────────────────────────────────────
        gpt52 = Model(
            name="GPT-5.2",
            version="2025-12-11",
            description="Multimodal LLM – flagship model",
            purpose="General-purpose text generation, analysis, and reasoning",
            model_type=ModelType.LLM,
            deployment=ModelDeployment.VENDOR_API,
            status=ModelStatus.APPROVED,
            risk_tier=RiskTier.TIER_2_HIGH,
            owner="AI Platform Team",
            business_unit="Wealth Management",
            provider_model_id="gpt-5.2-2025-12-11",
            context_window=128000,
            vendor_id=openai.id,
            sr_11_7_classification="Model",
            owasp_llm_risks={"applicable": ["LLM01", "LLM06", "LLM09"]},
        )
        claude = Model(
            name="Claude Opus 4.6",
            version="2026-02-03",
            description="Advanced reasoning model with enhanced safety",
            purpose="Complex analysis, summarization, code generation",
            model_type=ModelType.LLM,
            deployment=ModelDeployment.VENDOR_API,
            status=ModelStatus.UNDER_REVIEW,
            risk_tier=RiskTier.TIER_2_HIGH,
            owner="AI Platform Team",
            business_unit="Wealth Management",
            provider_model_id="claude-opus-4-2026-02-03",
            context_window=200000,
            vendor_id=anthropic.id,
        )
        gemini = Model(
            name="Gemini 3 Pro",
            version="2026-01-21",
            description="Multimodal model with 2M context, advanced reasoning & grounding",
            purpose="Long-context analysis, complex reasoning, multimodal understanding",
            model_type=ModelType.LLM,
            deployment=ModelDeployment.VENDOR_API,
            status=ModelStatus.APPROVED,
            risk_tier=RiskTier.TIER_2_HIGH,
            owner="AI Platform Team",
            business_unit="Wealth Management",
            provider_model_id="gemini-3-pro-2026-01-21",
            context_window=2000000,
            vendor_id=google.id,
            sr_11_7_classification="Model",
            owasp_llm_risks={"applicable": ["LLM01", "LLM06", "LLM09"]},
        )
        embeddings = Model(
            name="text-embedding-3-large",
            version="1.0",
            description="Document embedding model for RAG",
            model_type=ModelType.DEEP_LEARNING,
            deployment=ModelDeployment.VENDOR_API,
            status=ModelStatus.APPROVED,
            risk_tier=RiskTier.TIER_4_LOW,
            owner="AI Platform Team",
            vendor_id=openai.id,
        )
        session.add_all([gpt52, claude, gemini, embeddings])
        await session.flush()

        # ── Tools / EUCs ─────────────────────────────────────
        kb_search = Tool(
            name="Knowledge Base Search Tool",
            version="1.2",
            description="Searches the WM internal knowledge base for relevant documents",
            category=ToolCategory.AGENT_TOOL,
            criticality=ToolCriticality.MEDIUM,
            status=ToolStatus.ATTESTED,
            owner="AI Platform Team",
            last_attestation_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            next_attestation_date=datetime(2026, 7, 1, tzinfo=timezone.utc),
            agent_tool_config={"allowlisted": True, "sandboxed": False},
        )
        crm_tool = Tool(
            name="CRM Integration (Salesforce)",
            version="1.0",
            description="Saves meeting notes and action items to Salesforce",
            category=ToolCategory.API_SERVICE,
            criticality=ToolCriticality.HIGH,
            status=ToolStatus.ATTESTED,
            owner="WM Technology",
            last_attestation_date=datetime(2026, 1, 15, tzinfo=timezone.utc),
            next_attestation_date=datetime(2027, 1, 15, tzinfo=timezone.utc),
            agent_tool_config={"allowlisted": True, "requires_approval": True},
        )
        calculator = Tool(
            name="Portfolio Valuation Calculator",
            version="4.2",
            description="Excel-based portfolio valuation and risk metrics calculator",
            category=ToolCategory.EUC_SPREADSHEET,
            criticality=ToolCriticality.CRITICAL,
            status=ToolStatus.ATTESTED,
            owner="Portfolio Analytics",
            last_attestation_date=datetime(2025, 11, 15, tzinfo=timezone.utc),
            next_attestation_date=datetime(2026, 11, 15, tzinfo=timezone.utc),
        )
        fee_calc = Tool(
            name="Fee Calculator",
            version="5.1",
            description="Advisory fee calculation spreadsheet",
            category=ToolCategory.EUC_SPREADSHEET,
            criticality=ToolCriticality.CRITICAL,
            status=ToolStatus.ATTESTATION_OVERDUE,
            owner="Billing Operations",
            next_attestation_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        session.add_all([kb_search, crm_tool, calculator, fee_calc])
        await session.flush()

        # ── GenAI Use Cases ──────────────────────────────────
        assistant = GenAIUseCase(
            name="WM Assistant – Internal Q&A",
            version="2.1.0",
            description="RAG-based Q&A assistant for WM advisors – answers questions from internal knowledge base with mandatory citations",
            business_justification="Reduce research time for advisors by 40%, improve consistency of guidance",
            category=UseCaseCategory.RAG_QA,
            status=UseCaseStatus.MONITORING,
            risk_rating=RiskRating.HIGH,
            data_classification=DataClassification.CONFIDENTIAL,
            client_facing=False,
            uses_rag=True,
            uses_tools=True,
            requires_human_in_loop=False,
            owner="AI Platform Team",
            business_unit="Wealth Management",
            iso42001_phase="check",
            required_test_suites=["quality_correctness", "rag_groundedness", "safety_security", "red_team_promptfoo", "operational_controls", "regression"],
        )
        debrief = GenAIUseCase(
            name="Debrief – Meeting Summarizer",
            version="1.3.0",
            description="Summarizes client meeting transcripts into structured notes, action items, and follow-up emails",
            business_justification="Save 30 min per meeting for advisors, improve documentation quality",
            category=UseCaseCategory.SUMMARIZATION,
            status=UseCaseStatus.APPROVED,
            risk_rating=RiskRating.HIGH,
            data_classification=DataClassification.PII,
            client_facing=True,
            uses_tools=True,
            requires_human_in_loop=True,
            owner="WM Technology",
            business_unit="Wealth Management",
            iso42001_phase="do",
            required_test_suites=["quality_correctness", "safety_security", "red_team_promptfoo", "vulnerability_garak", "operational_controls", "regression"],
        )
        agent = GenAIUseCase(
            name="Research Agent – Multi-Step Analysis",
            version="0.5.0",
            description="Agentic workflow that performs multi-step research across knowledge bases, market data, and portfolio analytics",
            category=UseCaseCategory.AGENT_WORKFLOW,
            status=UseCaseStatus.TESTING,
            risk_rating=RiskRating.CRITICAL,
            data_classification=DataClassification.CONFIDENTIAL,
            uses_agents=True,
            uses_rag=True,
            uses_tools=True,
            uses_memory=True,
            requires_human_in_loop=True,
            owner="AI Platform Team",
            iso42001_phase="do",
            required_test_suites=["quality_correctness", "rag_groundedness", "safety_security", "red_team_promptfoo", "red_team_pyrit", "vulnerability_garak", "agentic_safety", "operational_controls", "regression"],
        )
        session.add_all([assistant, debrief, agent])
        await session.flush()

        # Link models and tools to use cases
        session.add_all([
            UseCaseModelLink(use_case_id=assistant.id, model_id=gpt52.id, role="primary"),
            UseCaseModelLink(use_case_id=assistant.id, model_id=embeddings.id, role="embedder"),
            UseCaseToolLink(use_case_id=assistant.id, tool_id=kb_search.id, purpose="Document retrieval"),
            UseCaseModelLink(use_case_id=debrief.id, model_id=gpt52.id, role="primary"),
            UseCaseToolLink(use_case_id=debrief.id, tool_id=crm_tool.id, purpose="Save to Salesforce"),
            UseCaseModelLink(use_case_id=agent.id, model_id=gpt52.id, role="primary"),
            UseCaseModelLink(use_case_id=agent.id, model_id=embeddings.id, role="embedder"),
            UseCaseToolLink(use_case_id=agent.id, tool_id=kb_search.id, purpose="Knowledge retrieval"),
        ])

        # ── Evaluation Runs ──────────────────────────────────
        eval1 = EvaluationRun(
            name="WM Assistant – Quality Suite v2.1",
            eval_type=EvalType.QUALITY_CORRECTNESS,
            status=EvalStatus.COMPLETED,
            use_case_id=assistant.id,
            model_id=gpt52.id,
            model_provider="openai",
            model_version="gpt-5.2-2025-12-11",
            started_at=datetime(2026, 2, 10, 10, 0, tzinfo=timezone.utc),
            completed_at=datetime(2026, 2, 10, 10, 15, tzinfo=timezone.utc),
            total_tests=50, passed=48, failed=2, errors=0, pass_rate=0.96,
            aggregate_scores={"accuracy": 0.96, "relevance": 0.94, "citations": 0.92},
        )
        eval2 = EvaluationRun(
            name="WM Assistant – Red Team (promptfoo)",
            eval_type=EvalType.RED_TEAM_PROMPTFOO,
            status=EvalStatus.COMPLETED,
            use_case_id=assistant.id,
            model_id=gpt52.id,
            model_provider="openai",
            model_version="gpt-5.2-2025-12-11",
            started_at=datetime(2026, 2, 10, 11, 0, tzinfo=timezone.utc),
            completed_at=datetime(2026, 2, 10, 11, 45, tzinfo=timezone.utc),
            total_tests=120, passed=115, failed=5, errors=0, pass_rate=0.958,
            owasp_category_results={
                "LLM01_Prompt_Injection": {"tested": 30, "passed": 28, "failed": 2},
                "LLM06_Sensitive_Disclosure": {"tested": 20, "passed": 19, "failed": 1},
                "LLM09_Misinformation": {"tested": 15, "passed": 14, "failed": 1},
            },
        )
        session.add_all([eval1, eval2])
        await session.flush()

        # ── Findings ─────────────────────────────────────────
        session.add_all([
            Finding(
                title="Prompt injection bypass in multi-turn conversation",
                severity=FindingSeverity.HIGH,
                status=FindingStatus.OPEN,
                source=FindingSource.RED_TEAM,
                use_case_id=assistant.id,
                owasp_risk_id="LLM01",
                mitre_atlas_technique="AML.T0051",
                remediation_owner="AI Platform Team",
                remediation_due_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
            ),
            Finding(
                title="PII detected in model output for account query",
                severity=FindingSeverity.CRITICAL,
                status=FindingStatus.IN_PROGRESS,
                source=FindingSource.EVALUATION,
                use_case_id=assistant.id,
                owasp_risk_id="LLM06",
                remediation_owner="AI Platform Team",
                remediation_due_date=datetime(2026, 2, 20, tzinfo=timezone.utc),
            ),
            Finding(
                title="Agent memory persistence exceeds approved TTL",
                severity=FindingSeverity.MEDIUM,
                status=FindingStatus.OPEN,
                source=FindingSource.EVALUATION,
                use_case_id=agent.id,
                owasp_risk_id="ASI06",
                nist_consideration="governance",
                remediation_owner="AI Platform Team",
            ),
        ])

        # ── Approvals ────────────────────────────────────────
        session.add_all([
            Approval(
                gate_type=ApprovalGateType.PRE_DEPLOYMENT,
                decision=ApprovalDecision.APPROVED,
                approver_role="model_risk_officer",
                approver_name="Jane Smith",
                rationale="All critical test suites passed. Risk rating high but mitigated by HITL controls.",
                use_case_id=assistant.id,
            ),
            Approval(
                gate_type=ApprovalGateType.PRODUCTION_RELEASE,
                decision=ApprovalDecision.CONDITIONAL,
                approver_role="technology_risk_committee",
                approver_name="Risk Committee",
                rationale="Approved with conditions.",
                conditions=["Quarterly recertification required", "Must resolve PII finding within 30 days"],
                use_case_id=debrief.id,
            ),
        ])

        # ── Monitoring Plans ─────────────────────────────────
        session.add(MonitoringPlan(
            name="WM Assistant – Daily Monitoring",
            use_case_id=assistant.id,
            cadence=MonitoringCadence.DAILY,
            canary_prompts=[
                {"prompt": "What is the firm's policy on client gifting?", "expected_contains": "gifting policy"},
                {"prompt": "Explain diversification benefits.", "expected_contains": "risk reduction"},
            ],
            thresholds={"faithfulness_min": 0.85, "toxicity_max": 0.05, "latency_p99_ms": 5000},
            alert_routing={"critical": ["slack:#ct-alerts"], "warning": ["slack:#ct-monitoring"]},
            recert_triggers={
                "model_version_change": True,
                "prompt_template_change": True,
                "corpus_change": True,
            },
        ))

        # ── Datasets ─────────────────────────────────────────
        session.add(Dataset(
            name="WM Golden Test Set",
            version="2.0",
            description="Curated test prompts covering portfolio, regulatory, compliance topics",
            dataset_type=DatasetType.GOLDEN_TEST_SET,
            record_count=50,
            contains_pii=False,
            data_classification="internal",
            format="jsonl",
        ))

        await session.commit()

    print("✅ Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
