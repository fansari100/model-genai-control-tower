"""Initial schema – all Control Tower domain tables.

Revision ID: 001_initial
Revises:
Create Date: 2026-02-14
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Vendors ──────────────────────────────────────────────
    op.create_table(
        "vendors",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("legal_entity", sa.String(255)),
        sa.Column("contract_id", sa.String(100)),
        sa.Column("contact_email", sa.String(255)),
        sa.Column("description", sa.Text),
        sa.Column("security_posture", sa.String(50), default="under_review"),
        sa.Column("sla_summary", sa.Text),
        sa.Column("data_processing_region", sa.String(100)),
        sa.Column("certifications", JSONB, default={}),
        sa.Column("redteam_due_diligence", JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("created_by", sa.String(255), default="system"),
        sa.Column("updated_by", sa.String(255), default="system"),
    )

    # ── Models ───────────────────────────────────────────────
    op.create_table(
        "models",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("version", sa.String(50), nullable=False, default="1.0.0"),
        sa.Column("description", sa.Text),
        sa.Column("purpose", sa.Text),
        sa.Column("model_type", sa.String(50), nullable=False),
        sa.Column("deployment", sa.String(50), default="vendor_api"),
        sa.Column("status", sa.String(50), default="draft"),
        sa.Column("risk_tier", sa.String(50), default="tier_3_medium"),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("business_unit", sa.String(100)),
        sa.Column("committee_path", sa.String(255)),
        sa.Column("provider_model_id", sa.String(255)),
        sa.Column("parameter_count", sa.Integer),
        sa.Column("context_window", sa.Integer),
        sa.Column("training_cutoff", sa.String(50)),
        sa.Column("inputs_description", sa.Text),
        sa.Column("outputs_description", sa.Text),
        sa.Column("known_limitations", sa.Text),
        sa.Column("aibom_artifact_id", sa.String(36)),
        sa.Column("sr_11_7_classification", sa.String(50)),
        sa.Column("nist_genai_considerations", JSONB, default={}),
        sa.Column("owasp_llm_risks", JSONB, default={}),
        sa.Column("mitre_atlas_techniques", JSONB, default=[]),
        sa.Column("metadata_extra", JSONB, default={}),
        sa.Column("vendor_id", sa.String(36), sa.ForeignKey("vendors.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("created_by", sa.String(255), default="system"),
        sa.Column("updated_by", sa.String(255), default="system"),
    )

    # ── Tools / EUCs ─────────────────────────────────────────
    op.create_table(
        "tools",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("version", sa.String(50), default="1.0"),
        sa.Column("description", sa.Text),
        sa.Column("purpose", sa.Text),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("criticality", sa.String(50), default="medium"),
        sa.Column("status", sa.String(50), default="under_review"),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("business_unit", sa.String(100)),
        sa.Column("custodian", sa.String(255)),
        sa.Column("technology_stack", sa.String(255)),
        sa.Column("location_path", sa.String(500)),
        sa.Column("inputs_description", sa.Text),
        sa.Column("outputs_description", sa.Text),
        sa.Column("upstream_dependencies", JSONB, default=[]),
        sa.Column("downstream_consumers", JSONB, default=[]),
        sa.Column("last_attestation_date", sa.DateTime(timezone=True)),
        sa.Column("next_attestation_date", sa.DateTime(timezone=True)),
        sa.Column("attestation_frequency_days", sa.Integer, default=365),
        sa.Column("attestation_owner", sa.String(255)),
        sa.Column("agent_tool_config", JSONB, default={}),
        sa.Column("metadata_extra", JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("created_by", sa.String(255), default="system"),
        sa.Column("updated_by", sa.String(255), default="system"),
    )

    # ── GenAI Use Cases ──────────────────────────────────────
    op.create_table(
        "genai_use_cases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("version", sa.String(50), default="1.0.0"),
        sa.Column("description", sa.Text),
        sa.Column("business_justification", sa.Text),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), default="draft"),
        sa.Column("risk_rating", sa.String(50), default="medium"),
        sa.Column("data_classification", sa.String(50), default="internal"),
        sa.Column("handles_pii", sa.Boolean, default=False),
        sa.Column("client_facing", sa.Boolean, default=False),
        sa.Column("uses_rag", sa.Boolean, default=False),
        sa.Column("uses_agents", sa.Boolean, default=False),
        sa.Column("uses_tools", sa.Boolean, default=False),
        sa.Column("uses_memory", sa.Boolean, default=False),
        sa.Column("requires_human_in_loop", sa.Boolean, default=True),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("business_unit", sa.String(100)),
        sa.Column("sponsor", sa.String(255)),
        sa.Column("committee_path", sa.String(255)),
        sa.Column("nist_governance_controls", JSONB, default={}),
        sa.Column("nist_content_provenance", JSONB, default={}),
        sa.Column("nist_predeployment_testing", JSONB, default={}),
        sa.Column("nist_incident_disclosure", JSONB, default={}),
        sa.Column("owasp_llm_top10_risks", JSONB, default={}),
        sa.Column("owasp_agentic_top10_risks", JSONB, default={}),
        sa.Column("iso42001_phase", sa.String(20)),
        sa.Column("required_test_suites", JSONB, default=[]),
        sa.Column("guardrail_config", JSONB, default={}),
        sa.Column("metadata_extra", JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("created_by", sa.String(255), default="system"),
        sa.Column("updated_by", sa.String(255), default="system"),
    )

    # ── Association Tables ───────────────────────────────────
    op.create_table(
        "use_case_model_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("use_case_id", sa.String(36), sa.ForeignKey("genai_use_cases.id"), nullable=False),
        sa.Column("model_id", sa.String(36), sa.ForeignKey("models.id"), nullable=False),
        sa.Column("role", sa.String(50), default="primary"),
        sa.Column("configuration", JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "use_case_tool_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("use_case_id", sa.String(36), sa.ForeignKey("genai_use_cases.id"), nullable=False),
        sa.Column("tool_id", sa.String(36), sa.ForeignKey("tools.id"), nullable=False),
        sa.Column("purpose", sa.String(255)),
        sa.Column("permission_scope", sa.String(100)),
        sa.Column("requires_approval", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ── Datasets ─────────────────────────────────────────────
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("version", sa.String(50), default="1.0"),
        sa.Column("description", sa.Text),
        sa.Column("dataset_type", sa.String(50), nullable=False),
        sa.Column("record_count", sa.Integer),
        sa.Column("contains_pii", sa.Boolean, default=False),
        sa.Column("data_classification", sa.String(50)),
        sa.Column("source_description", sa.Text),
        sa.Column("storage_location", sa.String(500)),
        sa.Column("artifact_hash", sa.String(64)),
        sa.Column("provenance", JSONB, default={}),
        sa.Column("schema_definition", JSONB, default={}),
        sa.Column("format", sa.String(50)),
        sa.Column("metadata_extra", JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("is_deleted", sa.Boolean, default=False),
        sa.Column("created_by", sa.String(255), default="system"),
        sa.Column("updated_by", sa.String(255), default="system"),
    )

    # ── Evaluation Runs ──────────────────────────────────────
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("eval_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column("use_case_id", sa.String(36), sa.ForeignKey("genai_use_cases.id")),
        sa.Column("model_id", sa.String(36), sa.ForeignKey("models.id")),
        sa.Column("dataset_id", sa.String(36)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("duration_seconds", sa.Float),
        sa.Column("worker_id", sa.String(100)),
        sa.Column("model_provider", sa.String(100)),
        sa.Column("model_version", sa.String(100)),
        sa.Column("prompt_template_hash", sa.String(64)),
        sa.Column("eval_config", JSONB, default={}),
        sa.Column("total_tests", sa.Integer, default=0),
        sa.Column("passed", sa.Integer, default=0),
        sa.Column("failed", sa.Integer, default=0),
        sa.Column("errors", sa.Integer, default=0),
        sa.Column("pass_rate", sa.Float),
        sa.Column("aggregate_scores", JSONB, default={}),
        sa.Column("owasp_category_results", JSONB, default={}),
        sa.Column("artifact_ids", JSONB, default=[]),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(255), default="system"),
        sa.Column("updated_by", sa.String(255), default="system"),
    )

    # ── Evaluation Results ───────────────────────────────────
    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("evaluation_runs.id"), nullable=False),
        sa.Column("test_case_id", sa.String(100), nullable=False),
        sa.Column("test_case_name", sa.String(255)),
        sa.Column("category", sa.String(100)),
        sa.Column("input_prompt", sa.Text),
        sa.Column("expected_output", sa.Text),
        sa.Column("actual_output", sa.Text),
        sa.Column("context_used", sa.Text),
        sa.Column("passed", sa.Boolean),
        sa.Column("score", sa.Float),
        sa.Column("threshold", sa.Float),
        sa.Column("metrics", JSONB, default={}),
        sa.Column("latency_ms", sa.Float),
        sa.Column("token_count_input", sa.Integer),
        sa.Column("token_count_output", sa.Integer),
        sa.Column("cost_usd", sa.Float),
        sa.Column("error_message", sa.Text),
        sa.Column("owasp_risk_id", sa.String(50)),
        sa.Column("metadata_extra", JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ── Findings ─────────────────────────────────────────────
    op.create_table(
        "findings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), default="open"),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("use_case_id", sa.String(36), sa.ForeignKey("genai_use_cases.id")),
        sa.Column("evaluation_run_id", sa.String(36)),
        sa.Column("model_id", sa.String(36)),
        sa.Column("tool_id", sa.String(36)),
        sa.Column("owasp_risk_id", sa.String(50)),
        sa.Column("mitre_atlas_technique", sa.String(100)),
        sa.Column("nist_consideration", sa.String(100)),
        sa.Column("evidence_description", sa.Text),
        sa.Column("evidence_artifact_ids", JSONB, default=[]),
        sa.Column("remediation_owner", sa.String(255)),
        sa.Column("remediation_plan", sa.Text),
        sa.Column("remediation_due_date", sa.DateTime(timezone=True)),
        sa.Column("remediation_completed_date", sa.DateTime(timezone=True)),
        sa.Column("metadata_extra", JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(255), default="system"),
        sa.Column("updated_by", sa.String(255), default="system"),
    )

    # ── Approvals ────────────────────────────────────────────
    op.create_table(
        "approvals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("gate_type", sa.String(50), nullable=False),
        sa.Column("decision", sa.String(50), nullable=False),
        sa.Column("approver_role", sa.String(100), nullable=False),
        sa.Column("approver_name", sa.String(255), nullable=False),
        sa.Column("approver_email", sa.String(255)),
        sa.Column("rationale", sa.Text),
        sa.Column("conditions", JSONB, default=[]),
        sa.Column("policy_input", JSONB, default={}),
        sa.Column("policy_output", JSONB, default={}),
        sa.Column("use_case_id", sa.String(36), sa.ForeignKey("genai_use_cases.id")),
        sa.Column("model_id", sa.String(36)),
        sa.Column("tool_id", sa.String(36)),
        sa.Column("evidence_artifact_ids", JSONB, default=[]),
        sa.Column("decision_hash", sa.String(64)),
        sa.Column("metadata_extra", JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(255), default="system"),
        sa.Column("updated_by", sa.String(255), default="system"),
    )

    # ── Monitoring Plans ─────────────────────────────────────
    op.create_table(
        "monitoring_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("use_case_id", sa.String(36), sa.ForeignKey("genai_use_cases.id"), nullable=False),
        sa.Column("status", sa.String(50), default="active"),
        sa.Column("cadence", sa.String(50), default="daily"),
        sa.Column("canary_prompts", JSONB, default=[]),
        sa.Column("regression_dataset_id", sa.String(36)),
        sa.Column("thresholds", JSONB, default={}),
        sa.Column("alert_routing", JSONB, default={}),
        sa.Column("recert_triggers", JSONB, default={}),
        sa.Column("metadata_extra", JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(255), default="system"),
        sa.Column("updated_by", sa.String(255), default="system"),
    )

    # ── Monitoring Executions ────────────────────────────────
    op.create_table(
        "monitoring_executions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("monitoring_plans.id"), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_seconds", sa.Float),
        sa.Column("metrics", JSONB, default={}),
        sa.Column("thresholds_breached", JSONB, default=[]),
        sa.Column("alerts_fired", JSONB, default=[]),
        sa.Column("drift_detected", sa.Boolean, default=False),
        sa.Column("recertification_triggered", sa.Boolean, default=False),
        sa.Column("artifact_ids", JSONB, default=[]),
        sa.Column("total_canaries", sa.Integer, default=0),
        sa.Column("canaries_passed", sa.Integer, default=0),
        sa.Column("metadata_extra", JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # ── Issues ───────────────────────────────────────────────
    op.create_table(
        "issues",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), default="open"),
        sa.Column("priority", sa.String(50), default="p3_medium"),
        sa.Column("use_case_id", sa.String(36)),
        sa.Column("finding_ids", JSONB, default=[]),
        sa.Column("owner", sa.String(255)),
        sa.Column("assignee", sa.String(255)),
        sa.Column("due_date", sa.DateTime(timezone=True)),
        sa.Column("resolved_date", sa.DateTime(timezone=True)),
        sa.Column("incident_disclosure", JSONB, default={}),
        sa.Column("remediation_plan", sa.Text),
        sa.Column("evidence_artifact_ids", JSONB, default=[]),
        sa.Column("metadata_extra", JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(255), default="system"),
        sa.Column("updated_by", sa.String(255), default="system"),
    )

    # ── Evidence Artifacts ───────────────────────────────────
    op.create_table(
        "evidence_artifacts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("artifact_type", sa.String(50), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("hash_algorithm", sa.String(20), default="sha256"),
        sa.Column("storage_bucket", sa.String(100), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(100), default="application/json"),
        sa.Column("size_bytes", sa.Integer),
        sa.Column("retention_tag", sa.String(50), default="standard"),
        sa.Column("retention_until", sa.DateTime(timezone=True)),
        sa.Column("worm_locked", sa.Boolean, default=False),
        sa.Column("previous_artifact_id", sa.String(36)),
        sa.Column("chain_hash", sa.String(64)),
        sa.Column("use_case_id", sa.String(36)),
        sa.Column("evaluation_run_id", sa.String(36)),
        sa.Column("approval_id", sa.String(36)),
        sa.Column("metadata_extra", JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_by", sa.String(255), default="system"),
        sa.Column("updated_by", sa.String(255), default="system"),
    )

    # ── pgvector extension (for document provenance & search) ─
    # Requires pgvector to be installed in the PostgreSQL instance.
    # In CI with pgvector/pgvector image, the extension is pre-installed.
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    except Exception:
        pass  # Extension may already exist or not be available


def downgrade() -> None:
    op.drop_table("evidence_artifacts")
    op.drop_table("issues")
    op.drop_table("monitoring_executions")
    op.drop_table("monitoring_plans")
    op.drop_table("approvals")
    op.drop_table("findings")
    op.drop_table("evaluation_results")
    op.drop_table("evaluation_runs")
    op.drop_table("datasets")
    op.drop_table("use_case_tool_links")
    op.drop_table("use_case_model_links")
    op.drop_table("genai_use_cases")
    op.drop_table("tools")
    op.drop_table("models")
    op.drop_table("vendors")
