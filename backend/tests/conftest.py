"""Pytest configuration and fixtures for Control Tower tests.

Uses Alembic migrations (not Base.metadata.create_all) to create the test
database schema. This ensures native PG enum types, indexes, and RLS
policies match the production schema exactly.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import app

# ── Database URLs ────────────────────────────────────────────────────────────
# Async URL for the test session (asyncpg)
TEST_DB_URL_ASYNC = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://ct_user:ct_password@localhost:5432/control_tower_test",
)
# Sync URL for Alembic migrations (psycopg2)
TEST_DB_URL_SYNC = os.environ.get(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg2://ct_user:ct_password@localhost:5432/control_tower_test",
)


def _run_alembic_upgrade(sync_url: str) -> None:
    """Run Alembic migrations against the test database using the sync driver."""
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
    command.upgrade(alembic_cfg, "head")


def _run_alembic_downgrade(sync_url: str) -> None:
    """Tear down all tables via Alembic downgrade."""
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
    command.downgrade(alembic_cfg, "base")


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean database session for each test.

    Schema is created via Alembic migrations (not metadata.create_all)
    to ensure native PG enum types match the ORM model definitions.
    """
    # Run Alembic migrations (sync driver)
    _run_alembic_upgrade(TEST_DB_URL_SYNC)

    # Create async engine for test session
    engine = create_async_engine(TEST_DB_URL_ASYNC, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    # Teardown: drop all tables via Alembic
    await engine.dispose()
    _run_alembic_downgrade(TEST_DB_URL_SYNC)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client with injected DB session."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
