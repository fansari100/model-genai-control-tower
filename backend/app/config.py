"""Application configuration – loaded from environment / .env file."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Central settings object – every service reads from here."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── General ──────────────────────────────────────────────
    environment: Environment = Environment.DEVELOPMENT
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]
    project_name: str = "Control Tower"

    # ── Postgres ─────────────────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "control_tower"
    postgres_user: str = "ct_user"
    postgres_password: str = "ct_password"
    database_url: str = ""
    database_url_sync: str = ""

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_async_db_url(cls, v: str, info: Any) -> str:
        if v:
            return v
        vals = info.data
        return (
            f"postgresql+asyncpg://{vals.get('postgres_user', 'ct_user')}"
            f":{vals.get('postgres_password', 'ct_password')}"
            f"@{vals.get('postgres_host', 'localhost')}"
            f":{vals.get('postgres_port', 5432)}"
            f"/{vals.get('postgres_db', 'control_tower')}"
        )

    @field_validator("database_url_sync", mode="before")
    @classmethod
    def assemble_sync_db_url(cls, v: str, info: Any) -> str:
        if v:
            return v
        vals = info.data
        return (
            f"postgresql+psycopg2://{vals.get('postgres_user', 'ct_user')}"
            f":{vals.get('postgres_password', 'ct_password')}"
            f"@{vals.get('postgres_host', 'localhost')}"
            f":{vals.get('postgres_port', 5432)}"
            f"/{vals.get('postgres_db', 'control_tower')}"
        )

    # ── MinIO / S3 ───────────────────────────────────────────
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_evidence: str = "ct-evidence"
    minio_bucket_artifacts: str = "ct-artifacts"
    minio_use_ssl: bool = False

    # ── Kafka / Redpanda ─────────────────────────────────────
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_audit: str = "ct.audit.events"
    kafka_topic_eval: str = "ct.eval.events"

    # ── Temporal ─────────────────────────────────────────────
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "control-tower"
    temporal_task_queue: str = "ct-governance"

    # ── OPA ───────────────────────────────────────────────────
    opa_url: str = "http://localhost:8181"
    opa_policy_path: str = "/v1/data/control_tower"

    # ── Keycloak ──────────────────────────────────────────────
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "control-tower"
    keycloak_client_id: str = "ct-frontend"
    keycloak_client_secret: str = "change-me"

    # ── OpenTelemetry ─────────────────────────────────────────
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "control-tower-backend"

    # ── Phoenix / Langfuse ────────────────────────────────────
    phoenix_endpoint: str = "http://localhost:6006"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3001"

    # ── LLM Providers ────────────────────────────────────────
    openai_api_key: str = ""
    openai_model: str = "gpt-5.2"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5-20260110"

    # ── Feature Flags ────────────────────────────────────────
    enable_otel: bool = True
    enable_kafka: bool = True
    enable_temporal: bool = True
    enable_opa: bool = True

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton settings instance."""
    return Settings()
