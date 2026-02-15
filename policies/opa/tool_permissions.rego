# ─────────────────────────────────────────────────────────────
# Control Tower – Tool Permission Policy
# ─────────────────────────────────────────────────────────────
# Controls which tools can be invoked, by whom, with what args.
# Implements least-privilege for agent tool access.
# ─────────────────────────────────────────────────────────────
package control_tower.tool_permissions

import rego.v1

default allow := false

# ── Tool permission matrix ───────────────────────────────────
# {tool_id: {allowed_roles: [...], requires_approval: bool, max_args: int}}
tool_permissions := {
    "search_knowledge_base": {
        "allowed_roles": ["analyst", "advisor", "agent", "admin"],
        "requires_approval": false,
        "sandboxed": false,
    },
    "retrieve_document": {
        "allowed_roles": ["analyst", "advisor", "agent", "admin"],
        "requires_approval": false,
        "sandboxed": false,
    },
    "save_to_crm": {
        "allowed_roles": ["advisor", "admin"],
        "requires_approval": true,
        "sandboxed": false,
    },
    "draft_email": {
        "allowed_roles": ["advisor", "agent", "admin"],
        "requires_approval": false,
        "sandboxed": true,
    },
    "calculate_portfolio_metrics": {
        "allowed_roles": ["analyst", "advisor", "admin"],
        "requires_approval": false,
        "sandboxed": true,
    },
    "execute_trade": {
        "allowed_roles": ["admin"],
        "requires_approval": true,
        "sandboxed": true,
    },
}

# ── Permission check ────────────────────────────────────────
tool_exists if {
    tool_permissions[input.tool_id]
}

role_allowed if {
    perm := tool_permissions[input.tool_id]
    input.caller_role in perm.allowed_roles
}

approval_satisfied if {
    perm := tool_permissions[input.tool_id]
    perm.requires_approval == false
}

approval_satisfied if {
    perm := tool_permissions[input.tool_id]
    perm.requires_approval == true
    input.arguments.approval_token != ""
}

# ── Master allow ─────────────────────────────────────────────
allow if {
    tool_exists
    role_allowed
    approval_satisfied
}

# ── Violations ───────────────────────────────────────────────
violations[msg] if {
    not tool_exists
    msg := sprintf("Tool '%s' is not registered in the permission matrix", [input.tool_id])
}

violations[msg] if {
    tool_exists
    not role_allowed
    msg := sprintf("Role '%s' is not authorized for tool '%s'", [input.caller_role, input.tool_id])
}

violations[msg] if {
    tool_exists
    role_allowed
    not approval_satisfied
    msg := sprintf("Tool '%s' requires approval but no approval token provided", [input.tool_id])
}

# ── Result ───────────────────────────────────────────────────
result := {
    "allow": allow,
    "violations": violations,
    "tool_id": input.tool_id,
    "caller_role": input.caller_role,
    "requires_sandbox": tool_permissions[input.tool_id].sandboxed,
}
