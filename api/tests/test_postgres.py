"""Behaviour that only a real PostgreSQL can prove: upsert, timestamptz and JSONB."""

from datetime import UTC, datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.football_data import FootballDataAdapter
from app.core.config import Settings
from app.models import Competition, Event, Season, Sport
from app.repositories.upsert import upsert_row
from app.services.sync_service import run_sync
from tests.conftest import PG_SESSION_TIME_ZONE, requires_postgres

pytestmark = requires_postgres

ISTANBUL = timezone(timedelta(hours=3))


async def _season(session: AsyncSession) -> int:
    sport = await upsert_row(session, Sport, {"slug": "football", "name": "Futbol"}, ["slug"])
    comp = await upsert_row(
        session,
        Competition,
        {"sport_id": sport, "source": "t", "external_id": "X", "slug": "x", "name": "X"},
        ["source", "external_id"],
    )
    return await upsert_row(
        session,
        Season,
        {"competition_id": comp, "year_label": "2026/27", "is_current": True},
        ["competition_id", "year_label"],
    )


def _event_values(season_id: int, **extra: object) -> dict:
    return {
        "season_id": season_id,
        "source": "t",
        "external_id": "1",
        "kind": "match",
        "start_time": datetime(2026, 10, 26, 20, 30, tzinfo=UTC),
        "status": "scheduled",
        "extra": {},
        **extra,
    }


async def test_session_runs_in_a_non_utc_zone(session: AsyncSession) -> None:
    assert await session.scalar(text("SHOW timezone")) == PG_SESSION_TIME_ZONE


async def test_column_types_are_timestamptz_and_jsonb(session: AsyncSession) -> None:
    rows = (
        await session.execute(
            text(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = current_schema() AND "
                "(table_name, column_name) IN (('events','start_time'),('events','extra'),"
                "('sync_runs','started_at'),('players','extra'),('standings','extra'))"
            )
        )
    ).all()
    types = {name: kind for name, kind in rows}
    assert types["start_time"] == "timestamp with time zone"
    assert types["started_at"] == "timestamp with time zone"
    assert types["extra"] == "jsonb"
    assert len(rows) == 5


async def test_upsert_is_idempotent_and_updates_in_place(session: AsyncSession) -> None:
    season = await _season(session)
    first = await upsert_row(session, Event, _event_values(season), ["source", "external_id"])
    second = await upsert_row(
        session, Event, _event_values(season, status="finished"), ["source", "external_id"]
    )
    await session.commit()
    assert first == second
    assert await session.scalar(select(func.count()).select_from(Event)) == 1
    assert await session.scalar(select(Event.status)) == "finished"


async def test_aware_datetimes_keep_their_instant(session: AsyncSession) -> None:
    season = await _season(session)
    kickoff = datetime(2026, 10, 26, 23, 30, tzinfo=ISTANBUL)  # 20:30 UTC
    await upsert_row(
        session, Event, _event_values(season, start_time=kickoff), ["source", "external_id"]
    )
    await session.commit()

    stored = await session.scalar(select(Event.start_time))
    assert stored == kickoff
    assert stored.utcoffset() == timedelta(0)  # returned as UTC, not as the Tokyo session zone
    utc_wall_clock = await session.scalar(text("SELECT start_time AT TIME ZONE 'UTC' FROM events"))
    assert utc_wall_clock == datetime(2026, 10, 26, 20, 30)


async def test_day_filter_uses_utc_boundaries(session: AsyncSession) -> None:
    season = await _season(session)
    for ext, hour in (("a", 23), ("b", 0)):  # 23:00 on the 26th and 00:00 on the 27th (UTC)
        day = 26 if hour == 23 else 27
        await upsert_row(
            session,
            Event,
            _event_values(
                season, external_id=ext, start_time=datetime(2026, 10, day, hour, tzinfo=UTC)
            ),
            ["source", "external_id"],
        )
    await session.commit()
    start = datetime(2026, 10, 26, tzinfo=UTC)
    count = await session.scalar(
        select(func.count())
        .select_from(Event)
        .where(Event.start_time >= start, Event.start_time < start + timedelta(days=1))
    )
    assert count == 1


async def test_jsonb_roundtrip_and_containment(session: AsyncSession) -> None:
    season = await _season(session)
    extra = {"winner": "HOME_TEAM", "half_time": {"home": 1, "away": 0}, "tags": ["derby"]}
    await upsert_row(session, Event, _event_values(season, extra=extra), ["source", "external_id"])
    await session.commit()

    assert await session.scalar(select(Event.extra)) == extra
    matches = await session.scalar(
        text("""SELECT count(*) FROM events WHERE extra @> '{"half_time": {"home": 1}}'::jsonb""")
    )
    assert matches == 1
    assert await session.scalar(text("SELECT jsonb_typeof(extra) FROM events")) == "object"


async def test_text_search_is_case_insensitive(seeded: async_sessionmaker[AsyncSession]) -> None:
    from app.repositories import queries

    async with seeded() as s:
        _, teams, _ = await queries.search(s, "ARSENAL")
    assert [t.name for t in teams] == ["Arsenal FC"]


async def test_full_sync_is_idempotent(
    maker: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    adapter = FootballDataAdapter(settings)
    await run_sync(maker, adapter, ("PL",))
    async with maker() as s:
        before = await s.scalar(select(func.count()).select_from(Event))
    run = await run_sync(maker, adapter, ("PL",))
    async with maker() as s:
        after = await s.scalar(select(func.count()).select_from(Event))
    assert run.status == "success"
    assert before == after == 120
