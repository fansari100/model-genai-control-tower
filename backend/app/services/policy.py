"""
Policy engine service – interfaces with OPA for policy-as-code decisions.

Implements approval gates, data classification, agent controls,
and tool permission policies.
"""

from __future__ import annotations

import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger()


class PolicyEngine:
    """Client for the Open Policy Agent (OPA) service."""

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.opa_url
        self.policy_path = settings.opa_policy_path
        self.enabled = settings.enable_opa

    async def evaluate(self, policy_name: str, input_data: dict) -> dict:
        """
        Evaluate a policy against input data.

        Args:
            policy_name: The policy to evaluate (e.g., "approval_gates")
            input_data: The input data for the policy decision

        Returns:
            Policy decision result
        """
        if not self.enabled:
            logger.warning("opa_disabled", policy=policy_name)
            return {"result": {"allow": True, "reason": "OPA disabled in config"}}

        url = f"{self.base_url}{self.policy_path}/{policy_name}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json={"input": input_data})
                response.raise_for_status()
                result = response.json()
                logger.info(
                    "opa_evaluation",
                    policy=policy_name,
                    result=result.get("result"),
                )
                return result
        except httpx.HTTPError as e:
            logger.error("opa_evaluation_failed", policy=policy_name, error=str(e))
            # Fail-closed: deny if OPA is unreachable
            return {
                "result": {
                    "allow": False,
                    "reason": f"Policy engine unavailable: {e}",
                    "error": True,
                }
            }

    async def check_approval_gate(
        self,
        risk_rating: str,
        test_pass_rate: float | None,
        open_critical_findings: int,
        required_mitigations_completed: bool,
    ) -> dict:
        """Check if a use case can pass the approval gate."""
        return await self.evaluate(
            "approval_gates",
            {
                "risk_rating": risk_rating,
                "test_pass_rate": test_pass_rate,
                "open_critical_findings": open_critical_findings,
                "required_mitigations_completed": required_mitigations_completed,
            },
        )

    async def check_data_classification(
        self,
        data_classification: str,
        handles_pii: bool,
        destination: str,
    ) -> dict:
        """Check if data classification rules allow the operation."""
        return await self.evaluate(
            "data_classification",
            {
                "data_classification": data_classification,
                "handles_pii": handles_pii,
                "destination": destination,
            },
        )

    async def check_agent_controls(
        self,
        agent_id: str,
        tool_calls: list[str],
        memory_writes: list[dict],
        execution_context: dict,
    ) -> dict:
        """Check agent control policies (OWASP Agentic Top 10 aligned)."""
        return await self.evaluate(
            "agent_controls",
            {
                "agent_id": agent_id,
                "tool_calls": tool_calls,
                "memory_writes": memory_writes,
                "execution_context": execution_context,
            },
        )

    async def check_tool_permissions(
        self,
        tool_id: str,
        caller_role: str,
        arguments: dict,
    ) -> dict:
        """Check if a tool call is permitted."""
        return await self.evaluate(
            "tool_permissions",
            {
                "tool_id": tool_id,
                "caller_role": caller_role,
                "arguments": arguments,
            },
        )


# Singleton
policy_engine = PolicyEngine()
