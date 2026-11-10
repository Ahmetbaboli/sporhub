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

from app.adapters.budget import reset_budgets
from app.adapters.football_data import FootballDataAdapter
from app.adapters.news_rss import RssNewsAdapter
from app.core import cache
from app.core.config import Settings, get_settings
from app.core.rate_limit import reset_rate_limits
from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.services.news_service import run_news_sync
from app.services.sync_service import run_sync

FIXTURE_TODAY = "2026-10-26"
TOKEN_SECRET = "test-shared-secret-that-is-at-least-32-bytes-long"
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


# Tests must never see the developer's real configuration: no .env file, no provider keys or
# feed lists from the shell environment.
Settings.model_config["env_file"] = None
ISOLATED_ENV = (
    "DATA_MODE", "DATABASE_URL", "REDIS_URL", "FOOTBALL_DATA_API_KEY", "THESPORTSDB_API_KEY",
    "BALLDONTLIE_API_KEY", "NEWS_FEEDS", "ADMIN_TOKEN", "API_TOKEN_SECRET", "SCHEDULER_ENABLED",
    "CORS_ORIGINS",
)  # fmt: skip

SETTINGS_CONSUMERS = (
    "app.core.config",
    "app.core.auth",
    "app.core.cache",
    "app.core.rate_limit",
    "app.core.redact",
    "app.db.session",
    "app.main",
    "app.routers.admin",
    "app.routers.v1",
    "app.scripts.check_sources",
    "app.scripts.purge_demo",
    "app.scripts.retag_news",
    "app.scripts.seed",
    "app.services.read_service",
)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        data_mode="demo",
        fixture_today=FIXTURE_TODAY,
        admin_token="test-admin-token",
        api_token_secret=TOKEN_SECRET,
        redis_url="",
        database_url="sqlite+aiosqlite://",
        rate_limit_per_minute=0,  # tests/test_rate_limit.py turns it on
    )


@pytest.fixture(autouse=True)
def _isolate(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    for name in ISOLATED_ENV:
        monkeypatch.delenv(name, raising=False)
    # Every module that imported get_settings by name: tests must never read the real .env.
    for module in SETTINGS_CONSUMERS:
        monkeypatch.setattr(f"{module}.get_settings", lambda: settings)
    cache.reset_cache()
    reset_budgets()
    reset_rate_limits()


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
    settings = Settings(data_mode="demo", fixture_today=FIXTURE_TODAY, redis_url="")
    await _create_tables(engine)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    await run_sync(maker, FootballDataAdapter(settings), ("PL", "CL"))
    await run_news_sync(maker, RssNewsAdapter(settings))
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
    if IS_POSTGRES:
        await _forget_users(engine)
    await engine.dispose()


# The seeded PostgreSQL schema is shared by every test, but API tests sign users in and save
# favorites into it; without this the next test would see them (SQLite copies a fresh file).
USER_TABLES = ("favorites", "users")  # children first


async def _forget_users(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        for table in USER_TABLES:
            await conn.execute(text(f"DELETE FROM {table}"))


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
