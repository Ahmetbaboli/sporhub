from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.football_data import FootballDataAdapter
from app.core.config import Settings
from app.services import scheduler
from app.services.sync_planner import (
    ROSTER_INTERVAL,
    SyncPlanner,
    competition_tiers,
    tier_for,
)
from app.services.sync_service import ALL_PARTS, SCORE_PARTS, run_sync

NOW = datetime(2026, 11, 2, 18, 0, tzinfo=UTC)


def ev(status: str, delta: timedelta, kind: str = "match") -> tuple[str, datetime, str]:
    return (status, NOW + delta, kind)


def test_tiers() -> None:
    assert tier_for([ev("live", -timedelta(minutes=30))], NOW, False) == "live"
    assert tier_for([ev("scheduled", timedelta(minutes=10))], NOW, False) == "live"
    assert tier_for([ev("scheduled", timedelta(hours=5))], NOW, False) == "today"
    assert tier_for([ev("finished", -timedelta(days=2))], NOW, False) == "idle"
    assert tier_for([ev("scheduled", timedelta(days=2), "race")], NOW, True) == "weekend"
    assert tier_for([], NOW, False) == "idle"


def test_planner_full_first_then_scores_by_tier_then_daily_full() -> None:
    p = SyncPlanner()
    assert p.due("fd", ["PL"], {}, NOW) == [("PL", ALL_PARTS)]  # never synced
    p.mark("fd", "PL", ALL_PARTS, NOW)
    assert p.due("fd", ["PL"], {"PL": "live"}, NOW + timedelta(minutes=1)) == []
    assert p.due("fd", ["PL"], {"PL": "live"}, NOW + timedelta(minutes=2)) == [("PL", SCORE_PARTS)]
    assert p.due("fd", ["PL"], {"PL": "idle"}, NOW + timedelta(hours=1)) == []
    assert p.due("fd", ["PL"], {"PL": "idle"}, NOW + ROSTER_INTERVAL) == [("PL", ALL_PARTS)]


def test_slow_providers_poll_less() -> None:
    p = SyncPlanner()
    p.mark("balldontlie", "NBA", ALL_PARTS, NOW)
    assert p.due("balldontlie", ["NBA"], {"NBA": "live"}, NOW + timedelta(minutes=5)) == []


async def test_tiers_from_database(
    maker: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    adapter = FootballDataAdapter(settings)
    await run_sync(maker, adapter, ("PL",))
    async with maker() as s:
        tiers = await competition_tiers(s, adapter, datetime.now(UTC))
    assert set(tiers) == {"PL"}
    assert tiers["PL"] in {"live", "today", "idle"}  # fixtures put matches around "today"


async def test_tick_skips_demo_and_unconfigured(monkeypatch, settings: Settings) -> None:
    calls: list[str] = []

    async def fake_run_sync(*args, **kwargs):
        calls.append("run")

    monkeypatch.setattr(scheduler, "run_sync", fake_run_sync)
    await scheduler.tick(settings, SyncPlanner())  # demo settings: nothing refreshed
    live_no_keys = settings.model_copy(
        update={
            "data_mode": "live",
            "football_data_api_key": "",
            "balldontlie_api_key": "",
            "thesportsdb_api_key": "",
        }  # fmt: skip
    )
    monkeypatch.setattr(scheduler, "adapter_names", lambda: ["football-data", "balldontlie"])
    await scheduler.tick(live_no_keys, SyncPlanner())
    assert calls == []
    assert scheduler.build_scheduler(settings).get_jobs() == []  # demo: no jobs at all
