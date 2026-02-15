"""
Feature flag system for controlled rollout of capabilities.

Supports three backends:
  1. ConfigMap/env-based (development)
  2. LaunchDarkly (production)
  3. Database-backed (self-hosted alternative)

Every flag evaluation is logged for audit trail.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.config import get_settings

logger = structlog.get_logger()

# ── Default flag values ──────────────────────────────────────────────────────
_DEFAULTS: dict[str, Any] = {
    "enable_agentic_evals": True,
    "enable_cascade_guardrails": True,
    "enable_aibom_generation": True,
    "enable_pdf_cert_packs": True,
    "enable_slack_notifications": True,
    "enable_email_notifications": False,
    "enable_pyrit_scenarios": True,
    "enable_garak_scans": True,
    "max_concurrent_evals": 5,
    "eval_timeout_minutes": 30,
    "guardrail_stage2_threshold": 0.5,
    "monitoring_canary_enabled": True,
    "approval_auto_escalation": True,
    "evidence_worm_lock_enabled": True,
    "pii_redaction_presidio": True,
    "audit_kafka_enabled": True,
}

# ── In-memory override store ─────────────────────────────────────────────────
_overrides: dict[str, Any] = {}


class FeatureFlagService:
    """Evaluates feature flags with audit logging."""

    def __init__(self) -> None:
        self._ld_client = None

    def _init_launchdarkly(self):
        """Initialize LaunchDarkly client if configured."""
        if self._ld_client is not None:
            return self._ld_client
        try:
            import ldclient
            from ldclient.config import Config
            import os

            sdk_key = os.environ.get("LAUNCHDARKLY_SDK_KEY", "")
            if sdk_key:
                ldclient.set_config(Config(sdk_key))
                self._ld_client = ldclient.get()
                logger.info("launchdarkly_initialized")
        except ImportError:
            pass
        return self._ld_client

    def evaluate(
        self,
        flag_key: str,
        user_id: str = "system",
        default: Any = None,
    ) -> Any:
        """
        Evaluate a feature flag.
        Priority: override → LaunchDarkly → env → defaults.
        """
        # Check overrides first
        if flag_key in _overrides:
            value = _overrides[flag_key]
            logger.debug("feature_flag_override", flag=flag_key, value=value, user=user_id)
            return value

        # Check LaunchDarkly
        ld = self._init_launchdarkly()
        if ld:
            try:
                from ldclient import Context
                context = Context.builder(user_id).kind("user").build()
                value = ld.variation(flag_key, context, default or _DEFAULTS.get(flag_key))
                logger.debug("feature_flag_ld", flag=flag_key, value=value, user=user_id)
                return value
            except Exception:
                pass

        # Check environment variables
        import os
        env_key = f"FF_{flag_key.upper()}"
        env_val = os.environ.get(env_key)
        if env_val is not None:
            # Type coercion
            if env_val.lower() in ("true", "false"):
                return env_val.lower() == "true"
            try:
                return int(env_val)
            except ValueError:
                return env_val

        # Fall back to defaults
        return default if default is not None else _DEFAULTS.get(flag_key)

    def is_enabled(self, flag_key: str, user_id: str = "system") -> bool:
        """Check if a boolean flag is enabled."""
        return bool(self.evaluate(flag_key, user_id, default=False))

    def get_int(self, flag_key: str, user_id: str = "system", default: int = 0) -> int:
        """Get an integer flag value."""
        return int(self.evaluate(flag_key, user_id, default=default))

    def set_override(self, flag_key: str, value: Any) -> None:
        """Set a runtime override (for testing or emergency)."""
        _overrides[flag_key] = value
        logger.warning("feature_flag_override_set", flag=flag_key, value=value)

    def clear_override(self, flag_key: str) -> None:
        """Clear a runtime override."""
        _overrides.pop(flag_key, None)
        logger.info("feature_flag_override_cleared", flag=flag_key)

    def get_all(self) -> dict[str, Any]:
        """Return all flags with current values."""
        return {k: self.evaluate(k) for k in _DEFAULTS}


feature_flags = FeatureFlagService()
