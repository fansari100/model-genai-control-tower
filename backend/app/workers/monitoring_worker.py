"""
Monitoring worker – executes scheduled monitoring checks.

Implements FINRA-aligned ongoing monitoring:
  - Canary prompt replay against live LLM endpoint
  - Regression detection via score comparison
  - Drift alerting against configurable thresholds
  - Recertification triggering
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

import httpx
import structlog

from app.config import get_settings

logger = structlog.get_logger()


class MonitoringWorker:
    """Executes monitoring plan checks against live endpoints."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def _call_llm(self, prompt: str) -> str:
        """
        Call the configured LLM provider and return the response text.
        Falls back gracefully if the provider is unreachable.
        """
        api_key = self._settings.openai_api_key
        model = self._settings.openai_model

        if not api_key:
            logger.debug("monitoring_llm_skip", reason="no API key configured")
            return ""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 512,
                        "temperature": 0,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning("monitoring_llm_call_failed", error=str(e))
            return ""

    async def execute_monitoring_plan(
        self,
        plan_id: str,
        canary_prompts: list[dict],
        thresholds: dict[str, float],
        recert_triggers: dict[str, bool],
    ) -> dict[str, Any]:
        """
        Execute a monitoring plan against live infrastructure.

        Steps:
        1. Replay canary prompts against the LLM endpoint and check responses.
        2. Compare measured metrics to configured thresholds.
        3. Determine if any thresholds are breached → drift detected.
        4. Evaluate recertification trigger conditions.
        """
        logger.info("monitoring_execution_start", plan_id=plan_id)
        start = time.monotonic()

        metrics: dict[str, float] = {}
        thresholds_breached: list[dict] = []
        alerts_fired: list[dict] = []
        canaries_passed = 0
        total_canaries = len(canary_prompts)

        # ── Step 1: Replay canary prompts ────────────────────
        for canary in canary_prompts:
            prompt = canary.get("prompt", "")
            expected_contains = canary.get("expected_contains", "")

            response = await self._call_llm(prompt)

            if not response:
                # LLM unreachable — count as failure to be safe
                continue

            passed = expected_contains.lower() in response.lower() if expected_contains else True
            if passed:
                canaries_passed += 1

        canary_pass_rate = canaries_passed / total_canaries if total_canaries > 0 else 1.0
        metrics["canary_pass_rate"] = canary_pass_rate

        # ── Step 2: Evaluate against thresholds ──────────────
        for metric_name, threshold_value in thresholds.items():
            current_value = metrics.get(metric_name)
            if current_value is None:
                continue

            breached = False
            direction = ""
            if metric_name.endswith("_min") and current_value < threshold_value:
                breached = True
                direction = "below_minimum"
            elif metric_name.endswith("_max") and current_value > threshold_value:
                breached = True
                direction = "above_maximum"
            elif not metric_name.endswith(("_min", "_max")):
                # Default: treat as minimum threshold
                if current_value < threshold_value:
                    breached = True
                    direction = "below_threshold"

            if breached:
                breach = {
                    "metric": metric_name,
                    "threshold": threshold_value,
                    "actual": current_value,
                    "direction": direction,
                }
                thresholds_breached.append(breach)
                alerts_fired.append(
                    {
                        "severity": "critical" if direction == "below_minimum" else "warning",
                        "message": f"{metric_name} = {current_value:.3f} breaches threshold {threshold_value}",
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )

        # ── Step 3: Drift detection ──────────────────────────
        drift_detected = len(thresholds_breached) > 0

        # ── Step 4: Recertification check ────────────────────
        recertification_triggered = False
        if drift_detected and recert_triggers.get("drift_detected", True):
            recertification_triggered = True
        if canary_pass_rate < 0.8:
            recertification_triggered = True

        duration = time.monotonic() - start

        result = {
            "plan_id": plan_id,
            "status": "completed",
            "executed_at": datetime.now(UTC).isoformat(),
            "duration_seconds": round(duration, 2),
            "metrics": metrics,
            "total_canaries": total_canaries,
            "canaries_passed": canaries_passed,
            "thresholds_breached": thresholds_breached,
            "alerts_fired": alerts_fired,
            "drift_detected": drift_detected,
            "recertification_triggered": recertification_triggered,
        }

        logger.info(
            "monitoring_execution_complete",
            plan_id=plan_id,
            drift=drift_detected,
            recert=recertification_triggered,
            canary_rate=f"{canary_pass_rate:.2%}",
            duration_s=f"{duration:.2f}",
        )

        return result
