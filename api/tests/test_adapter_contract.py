"""Contract every registered adapter must satisfy.

Adding a sport = a new adapter + registry line + fixtures; these tests then apply to it
automatically (they iterate the registry). If you add an adapter and a test here fails, the
adapter breaks the shared contract that sync_service and the API rely on.
"""

from datetime import timedelta, tzinfo

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.base import BaseAdapter
from app.adapters.dto import CompetitionDTO, EventDTO, StandingDTO, TeamDTO
from app.adapters.registry import ADAPTERS, adapter_names, create_adapter
from app.core.config import Settings
from app.models import Event, Sport, Standing, SyncRun, Team
from app.services import scheduler
from app.services.sync_service import run_sync

EVENT_KINDS = {"match", "race", "session"}
EVENT_STATUSES = {"scheduled", "live", "finished", "postponed", "cancelled"}
SHIFT = timedelta(days=7)

pytestmark = pytest.mark.parametrize("name", adapter_names())


def _adapter(name: str, settings: Settings) -> BaseAdapter:
    return create_adapter(name, settings)


async def _competitions(adapter: BaseAdapter) -> dict[str, CompetitionDTO]:
    return {c.external_id: c for c in await adapter.fetch_competitions()}


async def _bundle(adapter: BaseAdapter, comp: CompetitionDTO):
    assert comp.season_key
    season = comp.season_key
    return (
        await adapter.fetch_teams(comp.external_id, season),
        await adapter.fetch_events(comp.external_id, season),
        await adapter.fetch_standings(comp.external_id, season),
    )


def test_registry_identity(name: str, settings: Settings) -> None:
    adapter = _adapter(name, settings)
    assert adapter.source == name, "registry key must equal adapter.source"
    assert adapter.sport_slug and adapter.sport_name
    assert adapter.default_competitions
    assert adapter.use_fixtures and not adapter.fell_back_to_fixtures


async def test_competitions(name: str, settings: Settings) -> None:
    adapter = _adapter(name, settings)
    comps = await adapter.fetch_competitions()
    ids = [c.external_id for c in comps]
    assert len(ids) == len(set(ids)) and ids
    assert set(adapter.default_competitions) <= set(ids)
    for comp in comps:
        assert comp.name and comp.season_key and comp.season_label


async def test_teams_events_standings_are_well_formed(name: str, settings: Settings) -> None:
    adapter = _adapter(name, settings)
    comps = await _competitions(adapter)
    for ext_id in adapter.default_competitions:
        teams, events, standings = await _bundle(adapter, comps[ext_id])
        _check_teams(teams)
        _check_events(events, {t.external_id for t in teams})
        _check_standings(standings, {t.external_id for t in teams})


def _check_teams(teams: list[TeamDTO]) -> None:
    assert teams, "fixtures must contain teams"
    ids = [t.external_id for t in teams]
    assert len(ids) == len(set(ids)), "team external_ids must be unique"
    assert all(isinstance(i, str) and i and t.name for i, t in zip(ids, teams, strict=True))
    players = [p.external_id for t in teams for p in t.squad]
    assert len(players) == len(set(players)), "player external_ids must be unique"


def _check_events(events: list[EventDTO], team_ids: set[str]) -> None:
    assert events, "fixtures must contain events"
    ids = [e.external_id for e in events]
    assert len(ids) == len(set(ids)), "event external_ids must be unique"
    for event in events:
        assert event.kind in EVENT_KINDS and event.status in EVENT_STATUSES
        assert isinstance(event.start_time.tzinfo, tzinfo), "start_time must be timezone-aware"
        assert event.start_time.utcoffset() == timedelta(0), "start_time must be UTC"
        for p in event.participants:
            assert p.team is None or p.team.external_id in team_ids
        if event.status == "finished":
            assert event.participants, "finished events need participants"
            assert any(p.score is not None or p.position is not None for p in event.participants)
    assert {e.status for e in events} & {"finished"}, "fixtures need some finished events"
    assert {e.status for e in events} & {"scheduled", "live"}, "fixtures need upcoming events"


def _check_standings(standings: list[StandingDTO], team_ids: set[str]) -> None:
    assert standings, "fixtures must contain standings"
    for row in standings:
        assert row.position >= 1 and row.points >= 0
        assert row.team is not None or row.player_external_id
        if row.team:
            assert row.team.external_id in team_ids


async def test_fixture_dates_follow_the_pinned_today(name: str, settings: Settings) -> None:
    """Fixture mode must re-anchor every event date to FIXTURE_TODAY (and only then)."""
    moved_settings = settings.model_copy(
        update={"fixture_today": (_today(settings) + SHIFT).isoformat()}
    )
    base, moved = _adapter(name, settings), _adapter(name, moved_settings)
    comps = await _competitions(base)
    ext = base.default_competitions[0]
    season = comps[ext].season_key or ""
    before = {e.external_id: e.start_time for e in await base.fetch_events(ext, season)}
    after = {e.external_id: e.start_time for e in await moved.fetch_events(ext, season)}
    assert before.keys() == after.keys()
    assert all(after[k] - before[k] == SHIFT for k in before)


def _today(settings: Settings):
    from datetime import date

    return date.fromisoformat(settings.fixture_today)


async def test_sync_roundtrip_is_idempotent(
    name: str, settings: Settings, maker: async_sessionmaker[AsyncSession]
) -> None:
    adapter = _adapter(name, settings)
    first = await run_sync(maker, adapter)
    assert first.status == "success", first.error
    assert first.items_upserted > 0

    async def snapshot() -> dict[str, int]:
        async with maker() as s:
            return {
                m.__tablename__: await s.scalar(select(func.count()).select_from(m)) or 0
                for m in (Team, Event, Standing, SyncRun)
            }

    before = await snapshot()
    again = await run_sync(maker, adapter)
    after = await snapshot()
    assert again.status == "success"
    assert {k: v for k, v in before.items() if k != "sync_runs"} == {
        k: v for k, v in after.items() if k != "sync_runs"
    }
    async with maker() as s:
        slugs = set((await s.scalars(select(Sport.slug))).all())
    assert adapter.sport_slug in slugs


async def test_missing_key_falls_back_and_scheduler_skips(
    name: str, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    live = settings.model_copy(
        update={"use_fixtures": False, "football_data_api_key": "", "balldontlie_api_key": ""}
    )
    adapter = _adapter(name, live)
    needs_key = ADAPTERS[name].requires_api_key  # type: ignore[attr-defined]
    assert adapter.fell_back_to_fixtures is needs_key
    assert adapter.use_fixtures is needs_key
    await adapter.aclose()

    calls: list[str] = []

    async def fake_run_sync(*args: object, **kwargs: object) -> None:
        calls.append(name)

    monkeypatch.setattr(scheduler, "run_sync", fake_run_sync)
    await scheduler.sync_job(name, live)
    assert (calls == []) is needs_key, "keyless adapters must be skipped, keyed-free ones run"
