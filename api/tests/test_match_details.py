"""Match details: ESPN summary normalization and the on-demand /events/{id}/details endpoint."""

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.espn_soccer import BASE_URL, EspnSoccerAdapter, incident_kind
from app.adapters.football_data import FootballDataAdapter
from app.core.config import Settings
from app.db.session import get_session
from app.main import create_app
from app.models.events import Event
from app.services import match_service
from app.services.sync_service import run_sync

FINISHED = "401888258"  # Fenerbahçe 1-2 Göztepe, 2026-10-31 (real, trimmed)
UPCOMING = "401888256"
V1 = "/api/v1"
SUMMARY_URL = f"{BASE_URL}/site/v2/sports/soccer/tur.1/summary"


async def _client_for(maker: async_sessionmaker[AsyncSession]) -> AsyncClient:
    app = create_app()

    async def override() -> AsyncIterator[AsyncSession]:
        async with maker() as s:
            yield s

    app.dependency_overrides[get_session] = override
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _event_id(maker: async_sessionmaker[AsyncSession], external_id: str) -> int:
    async with maker() as s:
        return (await s.scalars(select(Event.id).where(Event.external_id == external_id))).one()


@pytest.fixture
async def espn_db(
    maker: async_sessionmaker[AsyncSession], settings: Settings
) -> async_sessionmaker[AsyncSession]:
    await run_sync(maker, EspnSoccerAdapter(settings), ("tur.1",))
    return maker


async def test_summary_normalizes_lineups_moments_and_stats(settings: Settings) -> None:
    details = await EspnSoccerAdapter(settings).fetch_match_details("tur.1", FINISHED)
    assert details is not None
    home, away = details.lineups
    assert (home.side, home.formation, len(home.starters)) == ("home", "4-2-3-1", 11)
    assert (away.side, away.formation) == ("away", "3-4-1-2")
    assert home.starters[0].position == "G" and home.substitutes
    goals = [(i.minute, i.side, i.player) for i in details.incidents if i.kind == "goal"]
    assert goals == [
        ("45'+1'", "home", "Matteo Guendouzi"),
        ("76'", "away", "Sinclair Armstrong"),
        ("78'", "away", "André Henrique"),
    ]
    sub = next(i for i in details.incidents if i.kind == "substitution")
    assert sub.player and sub.related_player  # on, off
    stats = {s.key: (s.home, s.away) for s in details.stats}
    assert stats["possession"] == (66, 34)
    assert stats["pass_accuracy"] == (83, 68)  # 442/530 and 175/258, not ESPN's rounded 0.8
    assert details.attendance is None  # ESPN reports 0 when unknown


async def test_pre_match_summary_is_empty_and_unknown_events_have_none(
    settings: Settings,
) -> None:
    adapter = EspnSoccerAdapter(settings)
    upcoming = await adapter.fetch_match_details("tur.1", UPCOMING)
    assert upcoming is not None and upcoming.is_empty()
    assert await adapter.fetch_match_details("tur.1", "no-such-fixture") is None


@pytest.mark.parametrize(
    ("raw", "kind"),
    [
        ({"scoringPlay": True, "type": {"type": "goal---header"}}, "goal"),
        ({"scoringPlay": True, "type": {"type": "penalty---scored"}}, "penalty_goal"),
        ({"scoringPlay": True, "type": {"type": "own-goal"}}, "own_goal"),
        ({"type": {"type": "yellow-red-card"}}, "red_card"),
        ({"type": {"type": "yellow-card"}}, "yellow_card"),
        ({"type": {"type": "kickoff"}}, None),
    ],
)
def test_incident_kinds(raw: dict, kind: str | None) -> None:
    assert incident_kind(raw) == kind


async def test_endpoint_serves_details_for_a_finished_match(
    espn_db: async_sessionmaker[AsyncSession],
) -> None:
    event_id = await _event_id(espn_db, FINISHED)
    async with await _client_for(espn_db) as client:
        body = (await client.get(f"{V1}/events/{event_id}/details")).json()
    assert body["available"] is True and body["source"] == "espn"
    assert [lu["side"] for lu in body["lineups"]] == ["home", "away"]
    assert body["stats"][0]["key"] == "possession"


async def test_far_future_match_is_not_fetched(espn_db: async_sessionmaker[AsyncSession]) -> None:
    event_id = await _event_id(espn_db, UPCOMING)
    async with espn_db() as s:
        later = datetime.now(UTC) + timedelta(days=2)
        await s.execute(update(Event).where(Event.id == event_id).values(start_time=later))
        await s.commit()
    async with await _client_for(espn_db) as client:
        body = (await client.get(f"{V1}/events/{event_id}/details")).json()
    assert body == {**body, "available": False, "reason": "not_started", "lineups": []}


async def test_sources_without_details_say_unsupported(
    maker: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    await run_sync(maker, FootballDataAdapter(settings), ("PL",))
    async with maker() as s:
        event_id = (await s.scalars(select(Event.id).limit(1))).one()
    async with await _client_for(maker) as client:
        body = (await client.get(f"{V1}/events/{event_id}/details")).json()
    assert body["available"] is False and body["reason"] == "unsupported"


async def test_unknown_event_is_404(maker: async_sessionmaker[AsyncSession]) -> None:
    async with await _client_for(maker) as client:
        r = await client.get(f"{V1}/events/999999/details")
    assert r.status_code == 404


@respx.mock
async def test_live_fetch_failure_degrades_and_is_not_cached(
    espn_db: async_sessionmaker[AsyncSession],
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    live = settings.model_copy(update={"data_mode": "live", "espn_enabled": True})
    monkeypatch.setattr("app.routers.v1.get_settings", lambda: live)
    monkeypatch.setattr("app.adapters.http.BACKOFF_MIN_SECONDS", 0)
    event_id = await _event_id(espn_db, FINISHED)
    async with espn_db() as s:  # rows synced in demo mode carry the "demo:" prefix
        await s.execute(update(Event).where(Event.id == event_id).values(source="espn"))
        await s.commit()
    route = respx.get(SUMMARY_URL).mock(return_value=httpx.Response(404))
    async with await _client_for(espn_db) as client:
        first = (await client.get(f"{V1}/events/{event_id}/details")).json()
        assert first["available"] is False and first["reason"] == "unavailable"
        fixture = (live.fixtures_dir / "espn" / f"summary_{FINISHED}.json").read_text("utf-8")
        route.mock(return_value=httpx.Response(200, json=json.loads(fixture)))
        second = (await client.get(f"{V1}/events/{event_id}/details")).json()
    assert second["available"] is True and route.call_count == 2


async def test_timeout_shows_unavailable(
    espn_db: async_sessionmaker[AsyncSession], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def never(*_: object) -> None:
        raise TimeoutError

    monkeypatch.setattr(EspnSoccerAdapter, "fetch_match_details", never)
    monkeypatch.setattr(match_service, "supports_details", lambda _source: True)
    event_id = await _event_id(espn_db, FINISHED)
    async with await _client_for(espn_db) as client:
        body = (await client.get(f"{V1}/events/{event_id}/details")).json()
    assert body["reason"] == "unavailable"
