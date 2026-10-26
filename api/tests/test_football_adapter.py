import httpx
import pytest
import respx

from app.adapters.football_data import (
    BASE_URL,
    STATUS_MAP,
    FootballDataAdapter,
    normalize_match,
    normalize_standings,
    season_label,
)
from app.adapters.http import RateLimitedClient
from app.core.config import Settings


@pytest.fixture
def adapter(settings: Settings) -> FootballDataAdapter:
    return FootballDataAdapter(settings)


async def test_competitions_normalized(adapter: FootballDataAdapter) -> None:
    comps = {c.external_id: c for c in await adapter.fetch_competitions()}
    assert set(comps) == {"PL", "PD", "SA", "BL1", "CL"}
    pl = comps["PL"]
    assert pl.name == "Premier League"
    assert pl.season_key == "2026"
    assert pl.season_label == "2026/27"


async def test_teams_include_squad(adapter: FootballDataAdapter) -> None:
    teams = await adapter.fetch_teams("PL", "2026")
    assert len(teams) == 20
    assert teams[0].squad and teams[0].squad[0].position == "Goalkeeper"
    assert teams[0].country == "England"


async def test_events_normalized_and_dates_shifted(adapter: FootballDataAdapter) -> None:
    events = await adapter.fetch_events("PL", "2026")
    assert {e.status for e in events} >= {"finished", "scheduled"}
    finished = next(e for e in events if e.status == "finished")
    home, away = finished.participants
    assert (home.side, away.side) == ("home", "away")
    assert home.score is not None and away.score is not None
    scheduled = next(e for e in events if e.status == "scheduled")
    assert scheduled.participants[0].score is None
    assert all(e.start_time.tzinfo is not None for e in events)


async def test_fixture_dates_follow_pinned_today(settings: Settings) -> None:
    shifted = FootballDataAdapter(settings.model_copy(update={"fixture_today": "2026-11-02"}))
    base = await FootballDataAdapter(settings).fetch_events("PL", "2026")
    moved = await shifted.fetch_events("PL", "2026")
    assert (moved[0].start_time - base[0].start_time).days == 7


async def test_standings_use_total_table(adapter: FootballDataAdapter) -> None:
    rows = await adapter.fetch_standings("PL", "2026")
    assert [r.position for r in rows] == list(range(1, 21))
    leader = rows[0]
    assert leader.points >= rows[-1].points
    assert leader.played == leader.won + leader.drawn + leader.lost
    assert "goal_difference" in leader.extra


def test_standings_ignore_non_total_tables() -> None:
    assert normalize_standings({"standings": [{"type": "HOME", "table": []}]}) == []


def test_status_mapping_is_complete() -> None:
    assert STATUS_MAP["TIMED"] == "scheduled"
    assert STATUS_MAP["PAUSED"] == "live"
    assert STATUS_MAP["AWARDED"] == "finished"
    assert STATUS_MAP["SUSPENDED"] == "postponed"


def test_normalize_match_handles_missing_score() -> None:
    event = normalize_match(
        {
            "id": 1,
            "utcDate": "2026-10-26T19:00:00Z",
            "status": "POSTPONED",
            "matchday": 3,
            "homeTeam": {"id": 1, "name": "A"},
            "awayTeam": {"id": 2, "name": "B"},
        }
    )
    assert event.status == "postponed"
    assert event.round == "3"
    assert [p.score for p in event.participants] == [None, None]


def test_season_label() -> None:
    assert season_label(2026) == "2026/27"
    assert season_label(2099) == "2099/00"


def test_missing_api_key_falls_back_to_fixtures(settings: Settings) -> None:
    adapter = FootballDataAdapter(
        settings.model_copy(update={"use_fixtures": False, "football_data_api_key": ""})
    )
    assert adapter.use_fixtures


@respx.mock
async def test_live_mode_sends_token_and_retries_on_429(settings: Settings) -> None:
    live = settings.model_copy(update={"use_fixtures": False, "football_data_api_key": "secret"})
    route = respx.get(f"{BASE_URL}/competitions").mock(
        side_effect=[
            httpx.Response(429),
            httpx.Response(200, json={"competitions": []}),
        ]
    )
    adapter = FootballDataAdapter(live)
    adapter._http = RateLimitedClient(  # speed up: no throttle, tiny backoff
        BASE_URL, headers={"X-Auth-Token": "secret"}, min_interval=0, backoff_min=0.01
    )
    assert await adapter.fetch_competitions() == []
    assert route.call_count == 2
    assert route.calls.last.request.headers["X-Auth-Token"] == "secret"
    await adapter.aclose()


@respx.mock
async def test_http_error_is_raised_after_retries() -> None:
    respx.get(f"{BASE_URL}/x").mock(return_value=httpx.Response(503))
    client = RateLimitedClient(BASE_URL, backoff_min=0.01)
    with pytest.raises(Exception, match="503"):
        await client.get_json("/x")
    await client.aclose()


@respx.mock
async def test_live_mode_never_shifts_dates(settings: Settings) -> None:
    """Date shifting is a fixture-only feature; real API timestamps must pass through untouched."""
    live = settings.model_copy(
        update={"use_fixtures": False, "football_data_api_key": "k", "fixture_today": "2030-01-01"}
    )
    raw = {
        "_fixture": {"reference_date": "2026-10-26"},  # even if a payload looked like a fixture
        "matches": [
            {
                "id": 7,
                "utcDate": "2026-03-01T15:00:00Z",
                "status": "FINISHED",
                "matchday": 1,
                "homeTeam": {"id": 1, "name": "A"},
                "awayTeam": {"id": 2, "name": "B"},
                "score": {"fullTime": {"home": 1, "away": 0}},
            }
        ],
    }
    respx.get(f"{BASE_URL}/competitions/PL/matches").mock(
        return_value=httpx.Response(200, json=raw)
    )
    adapter = FootballDataAdapter(live)
    assert not adapter.use_fixtures
    adapter._http = RateLimitedClient(BASE_URL, min_interval=0, backoff_min=0.01)
    (event,) = await adapter.fetch_events("PL", "2026")
    assert event.start_time.isoformat() == "2026-03-01T15:00:00+00:00"
    await adapter.aclose()
