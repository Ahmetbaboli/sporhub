import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, normalize_database_url
from app.core.startup import (
    ConfigurationError,
    check_settings,
    describe_validation_error,
    ensure_valid,
)
from app.db.dialect import try_scheduler_lock
from app.db.session import get_session
from app.main import create_app
from app.services.sync_service import run_sync
from tests.test_freshness import BrokenAdapter

SECRET = "do-not-print-this-secret-value"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "postgresql://u:p@ep-x.eu-central-1.aws.neon.tech/db?sslmode=require&channel_binding=require",
            "postgresql+asyncpg://u:p@ep-x.eu-central-1.aws.neon.tech/db?ssl=require",
        ),
        ("postgres://u:p@h:5432/db", "postgresql+asyncpg://u:p@h:5432/db"),
        ("postgresql+asyncpg://u:p@h/db", "postgresql+asyncpg://u:p@h/db"),
        ("sqlite+aiosqlite:///x.db", "sqlite+aiosqlite:///x.db"),
    ],
)
def test_database_url_is_normalised_for_asyncpg(raw: str, expected: str) -> None:
    assert normalize_database_url(raw) == expected
    assert Settings(database_url=raw).database_url == expected


def test_configuration_errors_name_the_variable_not_the_value(settings: Settings) -> None:
    bad = settings.model_copy(
        update={
            "admin_token": "change-me",
            "api_token_secret": "short",
            "cors_origins": "*",
            "news_feeds": [{"name": "x", "url": "http://insecure.test/rss"}],
        }
    )
    errors, _ = check_settings(bad)
    assert len(errors) == 4
    with pytest.raises(ConfigurationError) as exc:
        ensure_valid(bad)
    assert "ADMIN_TOKEN" in str(exc.value) and "change-me" not in str(exc.value)
    assert ensure_valid(settings) == []


def test_live_warnings(settings: Settings) -> None:
    live = settings.model_copy(
        update={"data_mode": "live", "thesportsdb_api_key": "123", "scheduler_enabled": True}
    )
    _, warnings = check_settings(live)
    assert any("THESPORTSDB_API_KEY" in w for w in warnings)
    assert any("SQLite" in w for w in warnings)
    no_news = live.model_copy(update={"news_feeds": []})
    assert any("NEWS_FEEDS" in w for w in check_settings(no_news)[1])


def test_validation_error_message_hides_values() -> None:
    with pytest.raises(ValidationError) as exc:
        Settings(data_mode=SECRET)  # type: ignore[arg-type]
    message = describe_validation_error(exc.value)
    assert "DATA_MODE" in message and SECRET not in message


async def test_health_ok_then_degraded(
    seeded: async_sessionmaker[AsyncSession], client: AsyncClient, settings: Settings, monkeypatch
) -> None:
    body = (await client.get("/health")).json()
    assert body["database"]["ok"] is True and body["data_mode"] == "demo"
    assert body["last_sync_at"] and body["redis"] is None  # no Redis configured in tests

    # A configured source whose last attempt failed makes the service "degraded" (still 200).
    keyed = settings.model_copy(update={"football_data_api_key": "configured-key"})
    monkeypatch.setattr("app.main.get_settings", lambda: keyed)
    app = create_app()

    async def override() -> AsyncIterator[AsyncSession]:
        async with seeded() as s:
            yield s

    app.dependency_overrides[get_session] = override
    await run_sync(seeded, BrokenAdapter(settings), ("PL",))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "degraded" and "football-data" in r.json()["stale_sources"]


async def test_health_down_is_503(client: AsyncClient, app) -> None:
    class Broken:
        async def execute(self, *a, **k):
            raise ConnectionError("db down")

    async def broken():
        yield Broken()

    app.dependency_overrides[get_session] = broken
    r = await client.get("/health")
    assert r.status_code == 503 and r.json()["status"] == "down"
    assert r.json()["database"] == {"ok": False, "detail": "ConnectionError", "ms": None}


async def test_sqlite_scheduler_lock_is_a_plain_connection(tmp_path) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'l.db'}")
    conn = await try_scheduler_lock(engine)
    assert conn is not None
    await conn.close()
    await engine.dispose()


@pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="needs PostgreSQL")
async def test_only_one_process_gets_the_scheduler_lock() -> None:
    url = os.environ["TEST_DATABASE_URL"]
    first_engine, second_engine = create_async_engine(url), create_async_engine(url)
    first = await try_scheduler_lock(first_engine)
    assert first is not None
    assert await try_scheduler_lock(second_engine) is None  # another replica: no scheduler
    await first.close()  # releasing lets the next replica take over
    taken_over = await try_scheduler_lock(second_engine)
    assert taken_over is not None
    await taken_over.close()
    await first_engine.dispose()
    await second_engine.dispose()


def test_every_settings_consumer_is_isolated_in_tests() -> None:
    """Guard: a new module importing get_settings by name must be added to conftest."""
    import pathlib

    from tests.conftest import SETTINGS_CONSUMERS

    app_dir = pathlib.Path(__file__).parents[1] / "app"
    consumers = {
        ".".join(path.relative_to(app_dir.parent).with_suffix("").parts)
        for path in app_dir.rglob("*.py")
        if "from app.core.config import" in (text := path.read_text(encoding="utf-8"))
        and "get_settings" in text.split("from app.core.config import", 1)[1].split("\n", 1)[0]
    }
    assert consumers <= set(SETTINGS_CONSUMERS) | {"app.core.config"}


def test_tests_do_not_read_dotenv() -> None:
    assert Settings.model_config["env_file"] is None
    assert Settings().football_data_api_key == ""


def test_rate_limit_without_internal_key_warns_and_short_key_fails() -> None:
    no_key = Settings(rate_limit_per_minute=120, internal_api_key="", redis_url="")
    assert any("INTERNAL_API_KEY" in w for w in check_settings(no_key)[1])
    short = Settings(internal_api_key="short", redis_url="")
    assert any("INTERNAL_API_KEY" in e for e in check_settings(short)[0])
    off = Settings(rate_limit_per_minute=0, internal_api_key="", redis_url="")
    assert not any("INTERNAL_API_KEY" in w for w in check_settings(off)[1])
