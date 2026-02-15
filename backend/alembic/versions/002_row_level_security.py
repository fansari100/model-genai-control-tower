"""Row-level security policies for business-unit data isolation.

Revision ID: 002_rls
Revises: 001_initial
Create Date: 2026-02-15
"""

from alembic import op

revision = "002_rls"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable RLS on sensitive tables
    for table in [
        "genai_use_cases", "models", "tools", "findings",
        "evaluation_runs", "approvals", "evidence_artifacts",
    ]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

        # Policy: users see only their business_unit's data
        # The app sets session variable: SET app.current_business_unit = 'WM'
        if table in ("genai_use_cases", "models", "tools"):
            op.execute(f"""
                CREATE POLICY {table}_bu_isolation ON {table}
                    USING (
                        business_unit = current_setting('app.current_business_unit', true)
                        OR current_setting('app.current_role', true) = 'admin'
                    )
            """)

        # Policy: findings visible to owner's BU + auditors
        if table == "findings":
            op.execute(f"""
                CREATE POLICY findings_visibility ON findings
                    USING (
                        created_by = current_setting('app.current_user', true)
                        OR current_setting('app.current_role', true) IN ('admin', 'auditor', 'model_risk_officer')
                    )
            """)

    # Performance indexes for common query patterns
    op.create_index("ix_models_status_risk", "models", ["status", "risk_tier"])
    op.create_index("ix_models_vendor_id", "models", ["vendor_id"])
    op.create_index("ix_tools_status_criticality", "tools", ["status", "criticality"])
    op.create_index("ix_tools_next_attestation", "tools", ["next_attestation_date"])
    op.create_index("ix_use_cases_status_risk", "genai_use_cases", ["status", "risk_rating"])
    op.create_index("ix_use_cases_owner", "genai_use_cases", ["owner"])
    op.create_index("ix_findings_severity_status", "findings", ["severity", "status"])
    op.create_index("ix_findings_use_case", "findings", ["use_case_id"])
    op.create_index("ix_eval_runs_use_case", "evaluation_runs", ["use_case_id"])
    op.create_index("ix_eval_runs_status", "evaluation_runs", ["status"])
    op.create_index("ix_evidence_use_case", "evidence_artifacts", ["use_case_id"])
    op.create_index("ix_evidence_type", "evidence_artifacts", ["artifact_type"])
    op.create_index("ix_approvals_use_case", "approvals", ["use_case_id"])
    op.create_index("ix_monitoring_use_case", "monitoring_plans", ["use_case_id"])
    op.create_index("ix_monitoring_exec_plan", "monitoring_executions", ["plan_id", "executed_at"])


def downgrade() -> None:
    for table in [
        "genai_use_cases", "models", "tools", "findings",
        "evaluation_runs", "approvals", "evidence_artifacts",
    ]:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    for idx in [
        "ix_models_status_risk", "ix_models_vendor_id",
        "ix_tools_status_criticality", "ix_tools_next_attestation",
        "ix_use_cases_status_risk", "ix_use_cases_owner",
        "ix_findings_severity_status", "ix_findings_use_case",
        "ix_eval_runs_use_case", "ix_eval_runs_status",
        "ix_evidence_use_case", "ix_evidence_type",
        "ix_approvals_use_case", "ix_monitoring_use_case",
        "ix_monitoring_exec_plan",
    ]:
        op.drop_index(idx)
