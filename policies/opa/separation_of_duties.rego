# ─────────────────────────────────────────────────────────────
# Control Tower – Separation of Duties (SoD) Policy
# ─────────────────────────────────────────────────────────────
# Enforces SR 11-7 "effective challenge" principle:
#   - Model developers cannot approve their own models
#   - Evaluators cannot approve use cases they evaluated
#   - Business owners cannot self-certify
#   - Environment promotion requires separate approvers
#
# Aligned with: SR 11-7 §§ III.B, III.C; ISO 42001 A.6.1.2
# ─────────────────────────────────────────────────────────────
package control_tower.separation_of_duties

import rego.v1

default allow := false

# ── Role hierarchy (least privilege) ──────────────────────────
role_hierarchy := {
    "readonly":             0,
    "business_user":        1,
    "evaluator":            2,
    "model_developer":      3,
    "model_risk_officer":   4,
    "admin":                5,
}

# ── SoD Rule 1: No self-approval ─────────────────────────────
# The person who created/owns an entity cannot approve it.
self_approval_violation if {
    input.action == "approve"
    input.entity_owner == input.approver_id
}

# ── SoD Rule 2: No self-evaluation approval ──────────────────
# The person who ran an evaluation cannot approve the use case
# based on that evaluation's results.
eval_approval_violation if {
    input.action == "approve"
    input.evaluation_run_by == input.approver_id
}

# ── SoD Rule 3: Developer cannot validate own model ──────────
# SR 11-7: "effective challenge" requires independent validation.
developer_validation_violation if {
    input.action == "validate"
    input.model_developer == input.validator_id
}

# ── SoD Rule 4: Environment promotion separation ─────────────
# Deployment to production requires a different person than the
# one who deployed to staging.
environment_promotion_violation if {
    input.action == "promote_to_production"
    input.staging_deployer == input.production_approver
}

# ── SoD Rule 5: Minimum approver count by risk tier ──────────
insufficient_approvers if {
    input.risk_rating == "critical"
    count(input.approvers) < 4
}

insufficient_approvers if {
    input.risk_rating == "high"
    count(input.approvers) < 3
}

insufficient_approvers if {
    input.risk_rating == "medium"
    count(input.approvers) < 2
}

# ── SoD Rule 6: Required role diversity ──────────────────────
# Critical/high use cases require approvers from at least 2
# distinct organizational roles.
approver_roles := {role |
    some approver in input.approvers
    role := approver.role
}

insufficient_role_diversity if {
    input.risk_rating in {"critical", "high"}
    count(approver_roles) < 2
}

# ── Master allow rule ────────────────────────────────────────
allow if {
    not self_approval_violation
    not eval_approval_violation
    not developer_validation_violation
    not environment_promotion_violation
    not insufficient_approvers
    not insufficient_role_diversity
}

# ── Violations (for audit trail) ─────────────────────────────
violations[msg] if {
    self_approval_violation
    msg := "SoD-001: Entity owner cannot approve their own entity (SR 11-7 §III.B effective challenge)"
}

violations[msg] if {
    eval_approval_violation
    msg := "SoD-002: Evaluator cannot approve use case based on their own evaluation results"
}

violations[msg] if {
    developer_validation_violation
    msg := "SoD-003: Model developer cannot independently validate their own model (SR 11-7 §III.C)"
}

violations[msg] if {
    environment_promotion_violation
    msg := "SoD-004: Production promotion requires different approver than staging deployer"
}

violations[msg] if {
    insufficient_approvers
    msg := sprintf("SoD-005: Insufficient approvers (%d) for %s risk tier", [count(input.approvers), input.risk_rating])
}

violations[msg] if {
    insufficient_role_diversity
    msg := sprintf("SoD-006: Insufficient role diversity (%d unique roles) — critical/high requires >= 2", [count(approver_roles)])
}

# ── Result ───────────────────────────────────────────────────
result := {
    "allow": allow,
    "violations": violations,
    "approver_count": count(input.approvers),
    "unique_roles": count(approver_roles),
    "policy": "separation_of_duties",
}
