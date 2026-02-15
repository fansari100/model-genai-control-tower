"""
Control Tower – FastAPI Application Entry Point

Unified Model, Tool & GenAI Control Tower for governance, certification,
and continuous monitoring of AI/ML models, GenAI use cases, and non-model tools.
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from prometheus_client import Counter, Histogram, make_asgi_app

from app import __version__
from app.api.router import api_router
from app.config import get_settings
from app.services.audit_events import audit_publisher
from app.utils.logging import setup_logging
from app.utils.otel import setup_telemetry

# Initialize structured logging immediately
setup_logging()
logger = structlog.get_logger()

# ── Prometheus Metrics ───────────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "ct_http_requests_total",
    "Total HTTP requests",
    ["method", "path_template", "status_code"],
)
REQUEST_DURATION = Histogram(
    "ct_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path_template"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan – startup and shutdown hooks."""
    settings = get_settings()

    # Startup
    logger.info(
        "control_tower_starting",
        version=__version__,
        environment=settings.environment.value,
    )

    # Initialize OpenTelemetry
    setup_telemetry()

    logger.info("control_tower_ready")

    yield

    # Shutdown
    await audit_publisher.close()
    logger.info("control_tower_shutting_down")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title="Control Tower – Model, Tool & GenAI Governance",
        description=(
            "Unified control plane for WM model inventory, GenAI use-case review, "
            "and continuous certification. Implements SR 11-7, NIST AI 600-1, "
            "OWASP LLM Top 10 (2025), OWASP Agentic Top 10 (2026), ISO/IEC 42001, "
            "and FINRA GenAI control expectations."
        ),
        version=__version__,
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── CORS ─────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request ID + Metrics Middleware ───────────────────────
    @app.middleware("http")
    async def metrics_and_request_id(request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()

        structlog.contextvars.bind_contextvars(request_id=request_id)

        response: Response = await call_next(request)

        duration = time.perf_counter() - start
        path_template = request.url.path
        # Strip UUIDs from path for metric cardinality control
        for part in path_template.split("/"):
            if len(part) == 36 and "-" in part:
                path_template = path_template.replace(part, "{id}")

        REQUEST_COUNT.labels(
            method=request.method,
            path_template=path_template,
            status_code=response.status_code,
        ).inc()
        REQUEST_DURATION.labels(
            method=request.method,
            path_template=path_template,
        ).observe(duration)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{duration * 1000:.1f}"

        structlog.contextvars.unbind_contextvars("request_id")
        return response

    # ── Prometheus metrics endpoint ──────────────────────────
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    # ── API routes ───────────────────────────────────────────
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    # ── Health check ─────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "ok",
            "version": __version__,
            "environment": settings.environment.value,
            "service": "control-tower-backend",
        }

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "service": "Control Tower – Model, Tool & GenAI Governance Platform",
            "version": __version__,
            "docs": "/docs",
            "health": "/health",
            "api": settings.api_v1_prefix,
        }

    return app


app = create_app()
