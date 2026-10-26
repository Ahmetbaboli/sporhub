from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.dto import CompetitionDTO
from app.adapters.football_data import FootballDataAdapter
from app.core.config import Settings
from app.models import (
    Competition,
    Event,
    EventParticipant,
    Player,
    Season,
    Sport,
    Standing,
    SyncRun,
    Team,
)
from app.services.sync_service import run_sync, slugify

TABLES = (Sport, Competition, Season, Team, Player, Event, EventParticipant, Standing)


async def counts(session: AsyncSession) -> dict[str, int]:
    return {
        m.__tablename__: await session.scalar(select(func.count()).select_from(m)) or 0
        for m in TABLES
    }


async def test_sync_populates_tables(
    maker: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    run = await run_sync(maker, FootballDataAdapter(settings), ("PL",))
    assert run.status == "success"
    assert run.items_upserted > 0
    async with maker() as s:
        c = await counts(s)
    assert c["competitions"] == 1
    assert c["teams"] == 20
    assert c["players"] == 20 * 15
    assert c["events"] == 120
    assert c["event_participants"] == 240
    assert c["standings"] == 20


async def test_sync_is_idempotent(
    maker: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    adapter = FootballDataAdapter(settings)
    await run_sync(maker, adapter, ("PL", "CL"))
    async with maker() as s:
        first = await counts(s)
    await run_sync(maker, adapter, ("PL", "CL"))
    async with maker() as s:
        second = await counts(s)
        runs = (await s.scalars(select(SyncRun))).all()
    assert first == second
    assert len(runs) == 2 and all(r.status == "success" for r in runs)


async def test_shared_team_is_not_duplicated_across_competitions(
    maker: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    await run_sync(maker, FootballDataAdapter(settings), ("PL", "CL"))
    async with maker() as s:
        arsenal = (await s.scalars(select(Team).where(Team.name == "Arsenal FC"))).all()
    assert len(arsenal) == 1


async def test_resync_updates_changed_event(
    maker: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    await run_sync(maker, FootballDataAdapter(settings), ("PL",))
    async with maker() as s:
        event = (await s.scalars(select(Event).where(Event.status == "scheduled"))).first()
        event.status = "cancelled"
        await s.commit()
        event_id = event.id
    await run_sync(maker, FootballDataAdapter(settings), ("PL",))
    async with maker() as s:
        assert (await s.get(Event, event_id)).status == "scheduled"


async def test_failing_competition_is_recorded_without_stopping_run(
    maker: async_sessionmaker[AsyncSession], settings: Settings, monkeypatch
) -> None:
    adapter = FootballDataAdapter(settings)
    original = adapter.fetch_events

    async def flaky(ext: str, season: str):
        if ext == "PL":
            raise RuntimeError("boom")
        return await original(ext, season)

    monkeypatch.setattr(adapter, "fetch_events", flaky)
    run = await run_sync(maker, adapter, ("PL", "PD"))
    assert run.status == "partial"
    assert "PL: boom" in (run.error or "")
    async with maker() as s:
        names = set((await s.scalars(select(Competition.external_id))).all())
    assert "PD" in names


async def test_fetch_failure_marks_run_failed(
    maker: async_sessionmaker[AsyncSession], settings: Settings, monkeypatch
) -> None:
    adapter = FootballDataAdapter(settings)

    async def broken() -> list[CompetitionDTO]:
        raise RuntimeError("api down")

    monkeypatch.setattr(adapter, "fetch_competitions", broken)
    run = await run_sync(maker, adapter)
    assert run.status == "failed"
    assert "api down" in (run.error or "")


def test_slugify() -> None:
    assert slugify("UEFA Champions League") == "uefa-champions-league"
    assert slugify("Süper Lig") == "super-lig"
