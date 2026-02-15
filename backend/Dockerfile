########################################################################
# Control Tower Backend – Multi-stage Docker Build
# Optimized with 'uv' for SOTA speed and dependency resolution (Feb 2026)
########################################################################
FROM python:3.13-slim AS builder

WORKDIR /app

# Install uv (SOTA Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# System deps for building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies using uv
# --system flag installs into site-packages, avoiding venv complexity in containers
COPY pyproject.toml .
RUN uv pip install --system --no-cache -e ".[dev]" || uv pip install --system --no-cache .

# ── Runtime Stage ─────────────────────────────────────────────────────
FROM python:3.13-slim AS runner

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# System deps for runtime (libpq for Postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
