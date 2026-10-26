"""Test fixtures.

The database is chosen by TEST_DATABASE_URL:
  * unset            -> SQLite (fast, no services needed)
  * postgresql+asyncpg://... -> real PostgreSQL; tests use two schemas ("work" per test,
    "seeded" once per session) and a non-UTC session time zone to catch timezone bugs.
"""

import asyncio
import os
import shutil
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, StaticPool

from app.adapters.football_data import FootballDataAdapter
from app.core import cache
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.services.sync_service import run_sync

FIXTURE_TODAY = "2026-10-26"
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "")
IS_POSTGRES = TEST_DATABASE_URL.startswith("postgresql")
WORK_SCHEMA = "work"
SEEDED_SCHEMA = "seeded"
# Deliberately not UTC: proves timestamptz handling does not depend on the session zone.
PG_SESSION_TIME_ZONE = "JST-9"  # POSIX form: valid even on builds without a tz database

requires_postgres = pytest.mark.skipif(not IS_POSTGRES, reason="needs TEST_DATABASE_URL=postgresql")


def _pg_engine(schema: str) -> AsyncEngine:
    return create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        connect_args={"server_settings": {"search_path": schema, "timezone": PG_SESSION_TIME_ZONE}},
    )


async def _recreate_schema(schema: str) -> None:
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
        await conn.execute(text(f"CREATE SCHEMA {schema}"))
    await engine.dispose()


async def _create_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        use_fixtures=True,
        fixture_today=FIXTURE_TODAY,
        admin_token="test-admin-token",
        redis_url="",
        database_url="sqlite+aiosqlite://",
    )


@pytest.fixture(autouse=True)
def _isolate(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setattr("app.core.config.get_settings", lambda: settings)
    monkeypatch.setattr("app.core.cache.get_settings", lambda: settings)
    monkeypatch.setattr("app.routers.admin.get_settings", lambda: settings)
    cache.reset_cache()


@pytest.fixture
async def maker() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """An empty database with the schema created; fresh for every test."""
    if IS_POSTGRES:
        await _recreate_schema(WORK_SCHEMA)
        engine = _pg_engine(WORK_SCHEMA)
    else:
        engine = create_async_engine(
            "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
        )
    await _create_tables(engine)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def session(maker: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with maker() as s:
        yield s


async def _seed(engine: AsyncEngine) -> None:
    settings = Settings(use_fixtures=True, fixture_today=FIXTURE_TODAY, redis_url="")
    await _create_tables(engine)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    await run_sync(maker, FootballDataAdapter(settings), ("PL", "CL"))
    await engine.dispose()


@pytest.fixture(scope="session")
def seeded_template(tmp_path_factory: pytest.TempPathFactory) -> Path | None:
    """Seed once per session: a SQLite file (copied per test) or the PostgreSQL "seeded" schema."""
    if IS_POSTGRES:
        asyncio.run(_recreate_schema(SEEDED_SCHEMA))
        asyncio.run(_seed(_pg_engine(SEEDED_SCHEMA)))
        return None
    path = tmp_path_factory.mktemp("seed") / "template.db"
    asyncio.run(_seed(create_async_engine(f"sqlite+aiosqlite:///{path}")))
    return path


@pytest.fixture
async def seeded(
    seeded_template: Path | None, tmp_path: Path
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """A database holding the football fixtures. Treat as read-only on PostgreSQL."""
    if IS_POSTGRES:
        engine = _pg_engine(SEEDED_SCHEMA)
    else:
        assert seeded_template is not None
        copy = tmp_path / "test.db"
        shutil.copy(seeded_template, copy)
        engine = create_async_engine(f"sqlite+aiosqlite:///{copy}")
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
def app(seeded: async_sessionmaker[AsyncSession]) -> FastAPI:
    application = create_app()

    async def override() -> AsyncIterator[AsyncSession]:
        async with seeded() as s:
            yield s

    application.dependency_overrides[get_session] = override
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
