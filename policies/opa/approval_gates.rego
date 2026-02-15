# ─────────────────────────────────────────────────────────────
# Control Tower – Approval Gate Policy
# ─────────────────────────────────────────────────────────────
# Determines whether a GenAI use case can proceed through
# governance approval gates based on risk rating, test outcomes,
# and open findings.
#
# Aligned with SR 11-7 "effective challenge" principles.
# ─────────────────────────────────────────────────────────────
package control_tower.approval_gates

import rego.v1

# ── Default deny ─────────────────────────────────────────────
default allow := false
default decision := "rejected"

# ── Approve: all conditions met ──────────────────────────────
allow if {
    no_critical_findings
    test_threshold_met
    mitigations_complete
}

# ── Decision logic ───────────────────────────────────────────
decision := "approved" if {
    allow
}

decision := "conditional" if {
    not allow
    not has_blocking_issues
    test_threshold_met
}

decision := "rejected" if {
    has_blocking_issues
}

# ── Helper rules ─────────────────────────────────────────────

# No open critical/high findings
no_critical_findings if {
    input.open_critical_findings == 0
}

# Test pass rate meets threshold for the risk tier
test_threshold_met if {
    input.risk_rating == "critical"
    input.test_pass_rate >= 0.98
}

test_threshold_met if {
    input.risk_rating == "high"
    input.test_pass_rate >= 0.95
}

test_threshold_met if {
    input.risk_rating == "medium"
    input.test_pass_rate >= 0.90
}

test_threshold_met if {
    input.risk_rating == "low"
    input.test_pass_rate >= 0.85
}

test_threshold_met if {
    input.risk_rating == "minimal"
    input.test_pass_rate >= 0.80
}

# All required mitigations are completed
mitigations_complete if {
    input.required_mitigations_completed == true
}

# Blocking issues
has_blocking_issues if {
    input.open_critical_findings > 0
}

has_blocking_issues if {
    not test_threshold_met
    input.risk_rating in {"critical", "high"}
}

# ── Required approvers based on risk ─────────────────────────
required_approvers[approver] if {
    input.risk_rating == "critical"
    approver := ["model_risk_officer", "chief_risk_officer", "technology_risk_committee", "business_line_head"][_]
}

required_approvers[approver] if {
    input.risk_rating == "high"
    approver := ["model_risk_officer", "technology_risk_committee", "business_line_head"][_]
}

required_approvers[approver] if {
    input.risk_rating == "medium"
    approver := ["model_risk_officer", "business_line_head"][_]
}

required_approvers[approver] if {
    input.risk_rating in {"low", "minimal"}
    approver := "model_control_analyst"
}

# ── Conditions for conditional approval ──────────────────────
conditions[msg] if {
    not no_critical_findings
    msg := "Must resolve all critical/high severity findings before production deployment"
}

conditions[msg] if {
    not mitigations_complete
    msg := "All required mitigations must be completed"
}

conditions[msg] if {
    input.risk_rating in {"critical", "high"}
    input.test_pass_rate < 0.98
    msg := sprintf("Test pass rate %.1f%% below threshold for %s risk tier", [input.test_pass_rate * 100, input.risk_rating])
}

# ── Audit output ─────────────────────────────────────────────
result := {
    "allow": allow,
    "decision": decision,
    "required_approvers": required_approvers,
    "conditions": conditions,
    "evaluated_at": "policy_engine",
}
