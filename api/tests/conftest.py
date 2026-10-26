import asyncio
import shutil
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.adapters.football_data import FootballDataAdapter
from app.core import cache
from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.services.sync_service import run_sync

FIXTURE_TODAY = "2026-10-26"


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
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.fixture
async def session(maker: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with maker() as s:
        yield s


@pytest.fixture(scope="session")
def seeded_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A SQLite file seeded once per test session; each test gets its own copy."""
    path = tmp_path_factory.mktemp("seed") / "template.db"
    settings = Settings(use_fixtures=True, fixture_today=FIXTURE_TODAY, redis_url="")

    async def build() -> None:
        engine = create_async_engine(f"sqlite+aiosqlite:///{path}")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await run_sync(
            async_sessionmaker(engine, expire_on_commit=False),
            FootballDataAdapter(settings),
            ("PL", "CL"),
        )
        await engine.dispose()

    asyncio.run(build())
    return path


@pytest.fixture
async def seeded(
    seeded_template: Path, tmp_path: Path
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
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
