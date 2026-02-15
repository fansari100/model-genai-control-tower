"""
External platform integration adapters.

Each adapter follows the same pattern:
  1. Abstract base class defining the interface
  2. Concrete implementation per target system
  3. Configuration via Vault secrets
  4. Structured logging + error handling
  5. Circuit breaker for resilience
"""
