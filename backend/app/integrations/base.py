"""Base classes for all external integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = structlog.get_logger()


class IntegrationError(Exception):
    """Base exception for integration failures."""

    def __init__(self, integration: str, operation: str, detail: str):
        self.integration = integration
        self.operation = operation
        self.detail = detail
        super().__init__(f"[{integration}] {operation}: {detail}")


class CircuitOpen(IntegrationError):
    """Circuit breaker is open — integration temporarily disabled."""
    pass


class CircuitBreaker:
    """Simple circuit breaker for external service calls."""

    def __init__(self, name: str, failure_threshold: int = 5, reset_timeout_seconds: int = 60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout_seconds
        self._failure_count = 0
        self._last_failure_time: float = 0
        self._state = "closed"  # closed, open, half-open

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = "closed"

    def record_failure(self) -> None:
        self._failure_count += 1
        import time
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.failure_threshold:
            self._state = "open"
            logger.warning("circuit_breaker_opened", integration=self.name, failures=self._failure_count)

    def allow_request(self) -> bool:
        if self._state == "closed":
            return True
        if self._state == "open":
            import time
            if time.monotonic() - self._last_failure_time > self.reset_timeout:
                self._state = "half-open"
                return True
            return False
        return True  # half-open: allow one probe


class BaseIntegration(ABC):
    """Abstract base for all external integrations."""

    def __init__(self, name: str):
        self.name = name
        self._circuit = CircuitBreaker(name)
        self._enabled = True

    @abstractmethod
    async def health_check(self) -> dict:
        """Check connectivity to the external system."""
        ...

    def _check_circuit(self) -> None:
        if not self._circuit.allow_request():
            raise CircuitOpen(self.name, "request", "circuit breaker is open")
