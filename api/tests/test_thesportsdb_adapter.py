from datetime import UTC, datetime

import httpx
import pytest
import respx

from app.adapters.http import RateLimitedClient
from app.adapters.thesportsdb import (
    BASE_URL,
    TheSportsDbAdapter,
    map_status,
    normalize_event,
    normalize_form,
    normalize_standing,
    season_label,
)
from app.core.config import Settings
from app.core.sources import source_by_name

# Shape copied from a real eventsseason.php item (2026-11-02).
EVENT = {
    "idEvent": "2527727",
    "strEvent": "Galatasaray vs Çorum",
    "dateEvent": "2026-08-14",
    "strTime": "18:30:00",
    "strTimestamp": "2026-08-14T18:30:00",
    "intHomeScore": "2",
    "intAwayScore": "2",
    "strStatus": "FT",
    "intRound": "1",
    "idHomeTeam": "133804",
    "idAwayTeam": "138951",
    "strHomeTeam": "Galatasaray",
    "strAwayTeam": "Çorum FK",
    "strVenue": "Rams Park",
    "strPostponed": "no",
}


def test_normalize_finished_event_is_utc() -> None:
    dto = normalize_event(EVENT)
    assert dto.start_time == datetime(2026, 8, 14, 18, 30, tzinfo=UTC)
    assert dto.status == "finished" and dto.round == "1" and dto.venue == "Rams Park"
    home, away = dto.participants
    assert (home.side, home.score, away.score) == ("home", 2, 2)
    assert away.team is not None and away.team.name == "Çorum FK"


@pytest.mark.parametrize(
    ("update", "status", "score"),
    [
        ({"strStatus": "NS", "intHomeScore": None, "intAwayScore": None}, "scheduled", None),
        ({"strStatus": "2H", "intHomeScore": "1", "intAwayScore": "0"}, "live", 1),
        ({"strStatus": "FT", "strPostponed": "yes", "intHomeScore": ""}, "postponed", None),
        ({"strStatus": "CANC", "intHomeScore": None}, "cancelled", None),
        ({"strStatus": "Match Finished"}, "finished", 2),
        ({"strStatus": "", "intHomeScore": None, "intAwayScore": None}, "scheduled", None),
    ],
)
def test_status_and_scores(update: dict, status: str, score: int | None) -> None:
    dto = normalize_event({**EVENT, **update})
    assert dto.status == status
    assert dto.participants[0].score == score  # no stale score on scheduled/postponed games


def test_missing_timestamp_falls_back_to_date_and_time() -> None:
    dto = normalize_event({**EVENT, "strTimestamp": None, "strTime": "17:00:00"})
    assert dto.start_time == datetime(2026, 8, 14, 17, 0, tzinfo=UTC)
    assert map_status({**EVENT, "strStatus": None, "dateEvent": "2099-01-01",
                       "strTimestamp": None}) == "scheduled"  # fmt: skip


def test_standing_row_and_form() -> None:
    row = {
        "intRank": "1", "idTeam": "133804", "strTeam": "Galatasaray", "strForm": "WWWWL",
        "intPlayed": "10", "intWin": "8", "intLoss": "1", "intDraw": "1", "intGoalsFor": "23",
        "intGoalsAgainst": "12", "intGoalDifference": "11", "intPoints": "25",
    }  # fmt: skip
    dto = normalize_standing(row)
    assert (dto.position, dto.played, dto.won, dto.drawn, dto.lost, dto.points) == (
        1, 10, 8, 1, 1, 25.0,
    )  # fmt: skip
    assert dto.extra["form"] == "W,W,W,W,L" and dto.extra["goal_difference"] == 11
    assert normalize_form(None) is None
    assert season_label("2026-2027") == "2026/27"


async def test_fixtures_are_real_turkish_leagues(settings: Settings) -> None:
    adapter = TheSportsDbAdapter(settings)
    comps = {c.external_id: c for c in await adapter.fetch_competitions()}
    assert comps["4339"].name == "Süper Lig" and comps["4339"].season_label == "2026/27"
    events = await adapter.fetch_events("4339", "2026-2027")
    assert events and all(e.start_time.tzinfo is UTC for e in events)
    names = {p.team.name for e in events for p in e.participants if p.team}
    assert "Galatasaray" in names


def test_development_key_is_not_a_live_configuration(settings: Settings) -> None:
    live = settings.model_copy(update={"data_mode": "live", "thesportsdb_api_key": "123"})
    assert not TheSportsDbAdapter(live).configured
    assert not source_by_name("thesportsdb").is_configured(live)
    paid = live.model_copy(update={"thesportsdb_api_key": "premium-key"})
    assert TheSportsDbAdapter(paid).configured


@respx.mock
async def test_live_requests_put_key_in_path(settings: Settings) -> None:
    live = settings.model_copy(update={"data_mode": "live", "thesportsdb_api_key": "pk"})
    route = respx.get(f"{BASE_URL}/pk/lookuptable.php").mock(
        return_value=httpx.Response(200, json={"table": None})
    )
    adapter = TheSportsDbAdapter(live)
    adapter._http = RateLimitedClient(BASE_URL, min_interval=0, backoff_min=0.01)
    assert await adapter.fetch_standings("4339", "2026-2027") == []  # null table -> empty
    assert route.calls.last.request.url.params["s"] == "2026-2027"
    await adapter.aclose()
