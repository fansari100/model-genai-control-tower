"""OpenTelemetry instrumentation setup for the Control Tower backend."""

from __future__ import annotations

import structlog

from app.config import get_settings

logger = structlog.get_logger()


def setup_telemetry() -> None:
    """Initialize OpenTelemetry tracing, metrics, and logging."""
    settings = get_settings()

    if not settings.enable_otel:
        logger.info("otel_disabled")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create(
            {
                "service.name": settings.otel_service_name,
                "service.version": "1.0.0",
                "deployment.environment": settings.environment.value,
            }
        )

        tracer_provider = TracerProvider(resource=resource)

        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            insecure=True,
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        trace.set_tracer_provider(tracer_provider)

        logger.info(
            "otel_initialized",
            endpoint=settings.otel_exporter_otlp_endpoint,
            service=settings.otel_service_name,
        )

    except ImportError as e:
        logger.warning("otel_import_error", error=str(e))
    except Exception as e:
        logger.error("otel_setup_error", error=str(e))
