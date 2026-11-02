from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.football_data import FootballDataAdapter
from app.core import cache
from app.core.config import Settings
from app.models import Event
from app.services.meta_service import STALE_AFTER, is_stale
from app.services.sync_service import run_sync

NOW = datetime(2026, 11, 2, 12, tzinfo=UTC)


def test_is_stale_rules() -> None:
    fresh = NOW - timedelta(minutes=5)
    assert not is_stale(True, fresh, fresh, "success", NOW)
    assert is_stale(True, fresh, NOW, "failed", NOW)  # last attempt failed
    assert is_stale(True, NOW - STALE_AFTER - timedelta(minutes=1), NOW, "success", NOW)
    assert not is_stale(False, None, None, None, NOW)  # not configured: nothing expected
    assert is_stale(True, None, NOW, "failed", NOW)


class BrokenAdapter(FootballDataAdapter):
    async def fetch_events(self, competition_ext_id: str, season: str):  # type: ignore[override]
        raise RuntimeError("provider is down")


async def test_provider_error_keeps_last_good_data_and_flags_it(
    seeded: async_sessionmaker[AsyncSession],
    client: AsyncClient,
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with seeded() as s:
        before = await s.scalar(select(func.count()).select_from(Event))
    run = await run_sync(seeded, BrokenAdapter(settings), ("PL",))
    assert run.status == "failed" and "provider is down" in (run.error or "")
    async with seeded() as s:
        assert await s.scalar(select(func.count()).select_from(Event)) == before

    keyed = settings.model_copy(update={"football_data_api_key": "configured-key"})
    monkeypatch.setattr("app.routers.v1.get_settings", lambda: keyed)
    await cache.get_cache().clear()
    events = await client.get("/api/v1/competitions/premier-league/events")
    assert events.status_code == 200 and events.json()["total"] > 0  # last good data served
    meta = (await client.get("/api/v1/meta")).json()
    source = next(s for s in meta["sources"] if s["name"] == "football-data")
    assert source["stale"] is True and source["last_status"] == "failed"
    assert source["last_success_at"] is not None
    assert source["scores_delayed"] is True
    comp = (await client.get("/api/v1/competitions/premier-league")).json()
    assert comp["source"] == "football-data" and comp["logo_url"] is None


async def test_admin_status(
    seeded: async_sessionmaker[AsyncSession], client: AsyncClient, settings: Settings
) -> None:
    await run_sync(seeded, BrokenAdapter(settings), ("PL",))
    assert (await client.get("/api/v1/admin/status")).status_code == 401
    r = await client.get("/api/v1/admin/status", headers={"X-Admin-Token": settings.admin_token})
    assert r.status_code == 200
    rows = {s["name"]: s for s in r.json()["sources"]}
    fd = rows["football-data"]
    assert fd["runs_24h"] >= 2 and fd["failures_24h"] >= 1
    assert 0 < fd["error_rate_24h"] <= 1
    assert "provider is down" in fd["last_error"]
    assert fd["budget"]["minute"]["limit"] == 9
    assert rows["jolpica"]["budget"]["hour"]["limit"] == 450
