import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command
from app.core.cache import MemoryCache, cached
from app.core.logging import JsonFormatter
from app.schemas.api import HealthOut

API_ROOT = Path(__file__).resolve().parents[1]


def test_migration_creates_all_tables(tmp_path: Path) -> None:
    db = tmp_path / "m.db"
    cfg = Config(str(API_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{db}")
    command.upgrade(cfg, "head")
    tables = set(inspect(create_engine(f"sqlite:///{db}")).get_table_names())
    assert {
        "sports",
        "competitions",
        "seasons",
        "teams",
        "players",
        "events",
        "event_participants",
        "standings",
        "sync_runs",
    } <= tables
    command.downgrade(cfg, "base")


async def test_memory_cache_roundtrip_and_ttl(monkeypatch) -> None:
    calls = 0

    async def loader() -> HealthOut:
        nonlocal calls
        calls += 1
        return HealthOut(status="ok", version="1")

    from app.core import cache

    monkeypatch.setattr(cache, "_backend", MemoryCache())
    await cached("k", HealthOut, loader, ttl=60)
    await cached("k", HealthOut, loader, ttl=60)
    assert calls == 1
    await cached("expired", HealthOut, loader, ttl=-1)
    await cached("expired", HealthOut, loader, ttl=-1)
    assert calls == 3


async def test_cache_failure_does_not_break_loader(monkeypatch) -> None:
    class Broken:
        async def get(self, key):
            raise ConnectionError("down")

        async def set(self, key, value, ttl):
            raise ConnectionError("down")

        async def clear(self):
            raise ConnectionError("down")

    from app.core import cache

    monkeypatch.setattr(cache, "_backend", Broken())

    async def loader() -> HealthOut:
        return HealthOut(status="ok", version="1")

    assert (await cached("k", HealthOut, loader)).status == "ok"
    await cache.invalidate_all()


def test_json_log_redacts_secrets() -> None:
    record = logging.LogRecord("t", logging.INFO, __file__, 1, "hi", None, None)
    record.token = "super-secret"
    record.path = "/x"
    out = json.loads(JsonFormatter().format(record))
    assert out["token"] == "***" and out["path"] == "/x" and out["msg"] == "hi"


def test_utc_datetime_type_normalizes() -> None:
    from app.db.base import UTCDateTime

    t = UTCDateTime()
    naive = datetime(2026, 1, 1, 12)
    assert t.process_bind_param(naive, None).tzinfo == UTC
    assert t.process_result_value(naive, None).tzinfo == UTC
