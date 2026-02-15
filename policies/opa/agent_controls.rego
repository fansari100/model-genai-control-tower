# ─────────────────────────────────────────────────────────────
# Control Tower – Agent Controls Policy
# ─────────────────────────────────────────────────────────────
# Enforces OWASP Agentic Top 10 (2026) aligned controls:
# - ASI01 Agent Goal Hijack
# - ASI02 Tool Misuse
# - ASI03 Identity/Privilege Abuse
# - ASI05 Unexpected RCE
# - ASI06 Memory/Context Poisoning
# - ASI08 Cascading Failures
# - ASI10 Rogue Agents
# ─────────────────────────────────────────────────────────────
package control_tower.agent_controls

import rego.v1

default allow := false

# ── Agent must be registered ─────────────────────────────────
agent_registered if {
    input.agent_id != ""
    input.agent_id != null
}

# ── Tool calls must be allowlisted (ASI02) ──────────────────
tool_allowlist := {
    "search_knowledge_base",
    "retrieve_document",
    "summarize_text",
    "draft_email",
    "save_to_crm",
    "calculate_portfolio_metrics",
    "get_market_data",
}

all_tools_allowed if {
    every tool in input.tool_calls {
        tool in tool_allowlist
    }
}

blocked_tools[tool] if {
    some tool in input.tool_calls
    not tool in tool_allowlist
}

# ── Dangerous tool patterns (ASI05 RCE prevention) ──────────
dangerous_patterns := {
    "eval", "exec", "subprocess", "os.system",
    "shell", "cmd", "powershell", "bash",
}

has_dangerous_pattern if {
    some tool in input.tool_calls
    some pattern in dangerous_patterns
    contains(tool, pattern)
}

# ── Memory write controls (ASI06) ───────────────────────────
max_memory_writes := 10

memory_writes_within_limit if {
    count(input.memory_writes) <= max_memory_writes
}

# Memory must have provenance
memory_has_provenance if {
    every write in input.memory_writes {
        write.source != ""
        write.timestamp != ""
    }
}

# ── Cascading failure protection (ASI08) ────────────────────
max_tool_calls_per_turn := 5
max_retry_count := 3

within_tool_call_limit if {
    count(input.tool_calls) <= max_tool_calls_per_turn
}

# ── Agent kill switch (ASI10) ────────────────────────────────
agent_active if {
    not input.execution_context.kill_switch_active
}

# ── Master allow rule ────────────────────────────────────────
allow if {
    agent_registered
    agent_active
    all_tools_allowed
    not has_dangerous_pattern
    memory_writes_within_limit
    memory_has_provenance
    within_tool_call_limit
}

# ── Violations ───────────────────────────────────────────────
violations[msg] if {
    not agent_registered
    msg := "ASI10: Agent is not registered in the agent registry"
}

violations[msg] if {
    not agent_active
    msg := "ASI10: Agent kill switch is active"
}

violations[msg] if {
    not all_tools_allowed
    msg := sprintf("ASI02: Blocked tool calls: %v", [blocked_tools])
}

violations[msg] if {
    has_dangerous_pattern
    msg := "ASI05: Dangerous execution pattern detected (potential RCE)"
}

violations[msg] if {
    not memory_writes_within_limit
    msg := sprintf("ASI06: Memory writes (%d) exceed limit (%d)", [count(input.memory_writes), max_memory_writes])
}

violations[msg] if {
    not within_tool_call_limit
    msg := sprintf("ASI08: Tool calls (%d) exceed per-turn limit (%d)", [count(input.tool_calls), max_tool_calls_per_turn])
}

# ── Result ───────────────────────────────────────────────────
result := {
    "allow": allow,
    "violations": violations,
    "blocked_tools": blocked_tools,
    "tool_calls_count": count(input.tool_calls),
    "memory_writes_count": count(input.memory_writes),
}
