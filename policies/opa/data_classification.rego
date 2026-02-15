# ─────────────────────────────────────────────────────────────
# Control Tower – Data Classification Policy
# ─────────────────────────────────────────────────────────────
# Enforces data handling rules based on classification level.
# Prevents PII from flowing to unapproved destinations.
# ─────────────────────────────────────────────────────────────
package control_tower.data_classification

import rego.v1

default allow := false

# ── Sensitivity levels ───────────────────────────────────────
sensitivity_level := 0 if input.data_classification == "public"
sensitivity_level := 1 if input.data_classification == "internal"
sensitivity_level := 2 if input.data_classification == "confidential"
sensitivity_level := 3 if input.data_classification == "pii"
sensitivity_level := 4 if input.data_classification == "restricted"

# ── Approved destinations by classification ──────────────────
approved_destinations := {
    "public": {"internal_llm", "vendor_llm", "external_api", "logging"},
    "internal": {"internal_llm", "vendor_llm_approved", "logging_redacted"},
    "confidential": {"internal_llm", "logging_redacted"},
    "pii": {"internal_llm_pii_approved", "logging_redacted"},
    "restricted": {"internal_llm_restricted"},
}

# ── Allow if destination is approved for classification ──────
allow if {
    destinations := approved_destinations[input.data_classification]
    destinations[input.destination]
}

# ── PII-specific rules ──────────────────────────────────────
pii_controls_required if {
    input.handles_pii == true
}

pii_controls_required if {
    input.data_classification == "pii"
}

requires_redaction if {
    pii_controls_required
    input.destination in {"logging", "logging_redacted", "vendor_llm_approved"}
}

requires_encryption if {
    sensitivity_level >= 2
}

# ── No client PII in prompts unless approved ─────────────────
deny_pii_in_prompts if {
    pii_controls_required
    not input.pii_approved
}

# ── Result ───────────────────────────────────────────────────
result := {
    "allow": allow,
    "sensitivity_level": sensitivity_level,
    "requires_redaction": requires_redaction,
    "requires_encryption": requires_encryption,
    "deny_pii_in_prompts": deny_pii_in_prompts,
}
