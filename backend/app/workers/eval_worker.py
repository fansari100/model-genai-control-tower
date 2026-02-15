"""
Evaluation worker – executes evaluation runs asynchronously.

Orchestrates:
- promptfoo quality/red-team evals
- garak vulnerability scans
- PyRIT security scenarios
- RAG groundedness checks
- Operational controls verification
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class EvalWorker:
    """Executes evaluation tasks dispatched by the API layer."""

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    async def run_promptfoo_eval(
        self,
        config_path: str,
        provider: str = "openai:gpt-4o",
        output_path: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute a promptfoo evaluation.

        Args:
            config_path: Path to promptfooconfig.yaml
            provider: Model provider string
            output_path: Where to save results

        Returns:
            Evaluation results dict
        """
        logger.info("promptfoo_eval_start", config=config_path, provider=provider)

        if output_path is None:
            output_path = tempfile.mktemp(suffix=".json")

        cmd = [
            "npx",
            "promptfoo@latest",
            "eval",
            "--config",
            config_path,
            "--output",
            output_path,
            "--no-cache",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                cwd=str(Path(config_path).parent),
            )

            if result.returncode != 0:
                logger.error("promptfoo_eval_failed", stderr=result.stderr[:500])
                return {"status": "failed", "error": result.stderr[:500]}

            with open(output_path) as f:
                results = json.load(f)

            logger.info("promptfoo_eval_complete", results_count=len(results.get("results", [])))
            return {"status": "completed", "results": results}

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Evaluation timed out after 600s"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def run_garak_scan(
        self,
        model_type: str = "openai",
        model_name: str = "gpt-4o",
        probes: str = "all",
        report_prefix: str = "ct_scan",
    ) -> dict[str, Any]:
        """
        Execute a garak LLM vulnerability scan.

        Returns:
            Scan results dict
        """
        logger.info("garak_scan_start", model=f"{model_type}:{model_name}")

        cmd = [
            "garak",
            "--model_type",
            model_type,
            "--model_name",
            model_name,
            "--probes",
            probes,
            "--report_prefix",
            report_prefix,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1200,
            )

            return {
                "status": "completed" if result.returncode == 0 else "failed",
                "stdout": result.stdout[-2000:],
                "stderr": result.stderr[-1000:] if result.returncode != 0 else "",
                "report_prefix": report_prefix,
            }
        except subprocess.TimeoutExpired:
            return {"status": "timeout"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def run_operational_controls_check(
        self,
        use_case_config: dict,
    ) -> dict[str, Any]:
        """
        Verify operational controls are in place (FINRA-aligned).

        Checks:
        - Prompt/output logging is active
        - Model version is recorded
        - Human-in-loop is enforced where required
        - PII redaction is active
        """
        checks: list[dict] = []

        # Check 1: Prompt/output logging
        checks.append(
            {
                "control": "prompt_output_logging",
                "description": "Prompt and output logging is captured (FINRA requirement)",
                "status": "pass" if use_case_config.get("logging_enabled") else "fail",
            }
        )

        # Check 2: Model version tracking
        checks.append(
            {
                "control": "model_version_tracking",
                "description": "Model version is recorded in every request (FINRA requirement)",
                "status": "pass" if use_case_config.get("version_tracking") else "fail",
            }
        )

        # Check 3: Human-in-loop
        requires_hitl = use_case_config.get("requires_human_in_loop", False)
        hitl_active = use_case_config.get("hitl_active", False)
        checks.append(
            {
                "control": "human_in_loop",
                "description": "Human-in-the-loop is enforced where required",
                "status": "pass" if (not requires_hitl or hitl_active) else "fail",
            }
        )

        # Check 4: PII redaction
        handles_pii = use_case_config.get("handles_pii", False)
        pii_redaction = use_case_config.get("pii_redaction_active", False)
        checks.append(
            {
                "control": "pii_redaction",
                "description": "PII redaction is active for PII-handling use cases",
                "status": "pass" if (not handles_pii or pii_redaction) else "fail",
            }
        )

        # Check 5: Tool permission controls (Agentic)
        uses_tools = use_case_config.get("uses_tools", False)
        tool_allowlist = use_case_config.get("tool_allowlist_active", False)
        checks.append(
            {
                "control": "tool_permission_controls",
                "description": "Tool allowlists enforced for tool-using systems",
                "status": "pass" if (not uses_tools or tool_allowlist) else "fail",
            }
        )

        passed = sum(1 for c in checks if c["status"] == "pass")
        total = len(checks)

        return {
            "status": "completed",
            "total_checks": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0,
            "checks": checks,
        }
