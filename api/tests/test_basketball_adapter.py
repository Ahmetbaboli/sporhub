import httpx
import pytest
import respx

from app.adapters.balldontlie import (
    BASE_URL,
    BallDontLieAdapter,
    current_season_year,
    normalize_game,
    normalize_status,
    season_label,
)
from app.adapters.http import RateLimitedClient
from app.core.config import Settings


@pytest.fixture
def adapter(settings: Settings) -> BallDontLieAdapter:
    return BallDontLieAdapter(settings)


def _live(settings: Settings, key: str = "bdl-key") -> BallDontLieAdapter:
    live = settings.model_copy(update={"use_fixtures": False, "balldontlie_api_key": key})
    adapter = BallDontLieAdapter(live)
    adapter._http = RateLimitedClient(
        BASE_URL, headers={"Authorization": key}, min_interval=0, backoff_min=0.01
    )
    return adapter


def test_season_helpers() -> None:
    from datetime import date

    assert current_season_year(date(2026, 10, 26)) == 2026
    assert current_season_year(date(2027, 3, 1)) == 2026
    assert season_label(2026) == "2026/27"


@pytest.mark.parametrize(
    ("state", "status"),
    [
        ("scheduled", "scheduled"),
        ("in_progress", "live"),
        ("delayed", "live"),
        ("final", "finished"),
        ("postponed", "postponed"),
        ("suspended", "postponed"),
        ("canceled", "cancelled"),
        ("unknown", "scheduled"),
    ],
)
def test_status_state_mapping(state: str, status: str) -> None:
    assert normalize_status({"status_state": state}) == status


def test_status_falls_back_to_text_when_state_missing() -> None:
    assert normalize_status({"status": "Final"}) == "finished"
    assert normalize_status({"status": "2026-10-27T00:00:00Z"}) == "scheduled"


def test_unplayed_games_have_no_score() -> None:
    team = {"id": 1, "full_name": "Atlanta Hawks", "name": "Hawks", "abbreviation": "ATL"}
    game = normalize_game(
        {
            "id": 9,
            "date": "2026-10-27",
            "datetime": "2026-10-28T00:00:00.000Z",
            "status_state": "scheduled",
            "home_team_score": 0,
            "visitor_team_score": 0,
            "home_team": team,
            "visitor_team": {**team, "id": 2, "full_name": "Boston Celtics"},
        }
    )
    assert [p.score for p in game.participants] == [None, None]
    assert [p.side for p in game.participants] == ["home", "away"]


async def test_teams_only_include_nba_franchises_with_rosters(adapter: BallDontLieAdapter) -> None:
    teams = await adapter.fetch_teams("nba", "2026")
    assert len(teams) == 30
    assert all(t.country == "USA" and t.short_name for t in teams)
    assert all(len(t.squad) == 13 for t in teams)
    player = teams[0].squad[0]
    assert player.name and player.extra.get("height")


async def test_games_events(adapter: BallDontLieAdapter) -> None:
    events = await adapter.fetch_events("nba", "2026")
    assert {e.status for e in events} == {"finished", "live", "scheduled"}
    assert events == sorted(events, key=lambda e: e.start_time)
    live = next(e for e in events if e.status == "live")
    assert all(p.score for p in live.participants) and live.extra["period"] == 3


async def test_standings_are_computed_from_regular_season_results(
    adapter: BallDontLieAdapter,
) -> None:
    standings = await adapter.fetch_standings("nba", "2026")
    events = await adapter.fetch_events("nba", "2026")
    assert [s.position for s in standings] == list(range(1, 31))
    finished = [e for e in events if e.status == "finished"]
    assert sum(s.won for s in standings) == len(finished) == sum(s.lost for s in standings)
    assert sum(s.extra["points_for"] for s in standings) == sum(
        s.extra["points_against"] for s in standings
    )
    for conference in ("East", "West"):
        ranks = [
            s.extra["conference_rank"] for s in standings if s.extra["conference"] == conference
        ]
        assert ranks == list(range(1, 16))
    pcts = [s.extra["win_pct"] for s in standings]
    assert pcts == sorted(pcts, reverse=True)


@respx.mock
async def test_live_mode_sends_raw_authorization_header_and_follows_cursor(
    settings: Settings,
) -> None:
    adapter = _live(settings)
    game = {
        "date": "2026-10-20",
        "datetime": "2026-10-20T23:30:00.000Z",
        "season": 2026,
        "postseason": False,
        "status": "Final",
        "status_state": "final",
        "home_team_score": 100,
        "visitor_team_score": 90,
        "home_team": {
            "id": 1,
            "full_name": "Atlanta Hawks",
            "name": "Hawks",
            "abbreviation": "ATL",
        },
        "visitor_team": {
            "id": 2,
            "full_name": "Boston Celtics",
            "name": "Celtics",
            "abbreviation": "BOS",
        },
    }

    def games(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("season_type") == "playoffs":
            return httpx.Response(200, json={"data": [], "meta": {"per_page": 100}})
        if request.url.params.get("cursor") is None:
            return httpx.Response(
                200, json={"data": [{**game, "id": 1}], "meta": {"next_cursor": 77}}
            )
        assert request.url.params["cursor"] == "77"
        return httpx.Response(200, json={"data": [{**game, "id": 2}], "meta": {}})

    route = respx.get(f"{BASE_URL}/games").mock(side_effect=games)
    events = await adapter.fetch_events("nba", "2026")
    assert [e.external_id for e in events] == ["1", "2"]
    first = route.calls[0].request
    assert first.headers["Authorization"] == "bdl-key"  # no "Bearer" prefix
    assert first.url.params["seasons[]"] == "2026"
    assert first.url.params["per_page"] == "100"
    await adapter.aclose()


@respx.mock
async def test_free_tier_without_active_players_still_syncs_teams(settings: Settings) -> None:
    adapter = _live(settings)
    team = {
        "id": 1,
        "conference": "East",
        "division": "Southeast",
        "city": "Atlanta",
        "name": "Hawks",
        "full_name": "Atlanta Hawks",
        "abbreviation": "ATL",
    }
    historic = {**team, "id": 99, "conference": "", "full_name": "Old Franchise"}
    respx.get(f"{BASE_URL}/teams").mock(
        return_value=httpx.Response(200, json={"data": [team, historic], "meta": {}})
    )
    respx.get(f"{BASE_URL}/players/active").mock(return_value=httpx.Response(401))
    teams = await adapter.fetch_teams("nba", "2026")
    assert [t.name for t in teams] == ["Atlanta Hawks"]
    assert teams[0].squad == []
    await adapter.aclose()


@respx.mock
async def test_live_mode_never_shifts_dates(settings: Settings) -> None:
    live = settings.model_copy(
        update={"use_fixtures": False, "balldontlie_api_key": "k", "fixture_today": "2030-01-01"}
    )
    adapter = BallDontLieAdapter(live)
    adapter._http = RateLimitedClient(BASE_URL, min_interval=0, backoff_min=0.01)
    payload = {
        "_fixture": {"reference_date": "2026-10-26"},
        "data": [
            {
                "id": 5,
                "date": "2026-03-01",
                "datetime": "2026-03-02T00:00:00.000Z",
                "status_state": "scheduled",
                "home_team": {"id": 1, "full_name": "A", "name": "A", "abbreviation": "A"},
                "visitor_team": {"id": 2, "full_name": "B", "name": "B", "abbreviation": "B"},
            }
        ],
        "meta": {},
    }
    respx.get(f"{BASE_URL}/games").mock(return_value=httpx.Response(200, json=payload))
    (event, *_) = await adapter.fetch_events("nba", "2026")
    assert event.start_time.isoformat() == "2026-03-02T00:00:00+00:00"
    await adapter.aclose()
