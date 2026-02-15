"""Pytest configuration and fixtures for Control Tower tests.

Uses Alembic migrations to create the test database schema, ensuring
native PG enum types match production exactly.
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
from sqlalchemy import create_engine

from app.database import get_db
from app.main import app

# ── Database URLs ────────────────────────────────────────────
TEST_DB_URL_ASYNC = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://ct_user:ct_password@localhost:5432/control_tower_test",
)
TEST_DB_URL_SYNC = os.environ.get(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg2://ct_user:ct_password@localhost:5432/control_tower_test",
)


def _clean_database(sync_url: str) -> None:
    """Drop all tables, types, and extensions — total clean slate."""
    engine = create_engine(sync_url)
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO PUBLIC"))
        conn.commit()
    engine.dispose()


def _run_alembic_upgrade(sync_url: str) -> None:
    """Run Alembic migrations to head."""
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
    command.upgrade(alembic_cfg, "head")


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean database session per test via Alembic migrations."""
    # Clean slate → migrate → test → clean slate
    _clean_database(TEST_DB_URL_SYNC)
    _run_alembic_upgrade(TEST_DB_URL_SYNC)

    engine = create_async_engine(TEST_DB_URL_ASYNC, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()
    _clean_database(TEST_DB_URL_SYNC)


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
