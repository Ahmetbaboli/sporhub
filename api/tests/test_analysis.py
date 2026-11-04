from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core import cache
from app.schemas.analysis import FormEntry
from app.schemas.api import TeamOut
from app.services.analysis_service import current_streak, main_season, summarize

V1 = "/api/v1"
OPPONENT = TeamOut(id=99, name="Rakip")


def entry(scored: int, conceded: int, side: str = "home") -> FormEntry:
    result = "W" if scored > conceded else "L" if scored < conceded else "D"
    return FormEntry(
        event_id=1,
        start_time=datetime(2026, 1, 1, tzinfo=UTC),
        competition="Lig",
        side=side,
        opponent=OPPONENT,
        scored=scored,
        conceded=conceded,
        result=result,
    )


def test_summarize_counts_and_averages() -> None:
    stats = summarize([entry(2, 0), entry(1, 1), entry(0, 3, "away"), entry(4, 1)])
    assert (stats.played, stats.won, stats.drawn, stats.lost) == (4, 2, 1, 1)
    assert (stats.scored, stats.conceded, stats.clean_sheets) == (7, 5, 1)
    assert stats.win_pct == 0.5
    assert stats.avg_scored == 1.75


def _played_in(*seasons: Any) -> list[Any]:
    """(event, entry) pairs, newest first, one per season given."""
    return [(SimpleNamespace(season=s, season_id=s.id), entry(1, 0)) for s in seasons]


def test_main_season_prefers_the_league_over_a_recent_cup_night() -> None:
    # Galatasaray: last match in the Champions League, but ten league games this season.
    league = SimpleNamespace(id=1, is_current=True)
    europe = SimpleNamespace(id=2, is_current=True)
    pairs = _played_in(europe, league, europe, league, league, europe, league)
    assert main_season(pairs) is league  # type: ignore[arg-type]


def test_main_season_ignores_old_seasons_and_breaks_ties_by_recency() -> None:
    old = SimpleNamespace(id=1, is_current=False)
    new_cup = SimpleNamespace(id=2, is_current=True)
    new_league = SimpleNamespace(id=3, is_current=True)
    pairs = _played_in(new_cup, new_league, old, old, old)
    assert main_season(pairs) is new_cup  # type: ignore[arg-type]
    # No season flagged current: the latest match's season.
    a, b = SimpleNamespace(id=4, is_current=False), SimpleNamespace(id=5, is_current=False)
    assert main_season(_played_in(a, b, b)) is a  # type: ignore[arg-type]


def test_summarize_empty_is_zero() -> None:
    assert summarize([]).played == 0


def test_streak_counts_leading_results() -> None:
    assert current_streak([entry(1, 0), entry(2, 1), entry(0, 0)]) == "W2"
    assert current_streak([entry(0, 1)]) == "L1"
    assert current_streak([]) is None


@pytest.fixture(autouse=True)
async def _data(seeded: async_sessionmaker) -> None:
    await cache.get_cache().clear()


async def _football_team_id(client: AsyncClient) -> int:
    teams = (await client.get(f"{V1}/teams", params={"sport": "football"})).json()["items"]
    return teams[0]["id"]


async def test_team_analysis_is_consistent(client: AsyncClient) -> None:
    team_id = await _football_team_id(client)
    r = await client.get(f"{V1}/teams/{team_id}/analysis", params={"last": 5})
    assert r.status_code == 200
    body = r.json()
    assert 0 < len(body["form"]) <= 5
    times = [e["start_time"] for e in body["form"]]
    assert times == sorted(times, reverse=True)
    overall, home, away = body["overall"], body["home"], body["away"]
    assert overall["played"] == overall["won"] + overall["drawn"] + overall["lost"]
    assert overall["played"] == home["played"] + away["played"]
    assert overall["scored"] == home["scored"] + away["scored"]
    assert body["streak"][0] == body["form"][0]["result"]
    assert all(e["opponent"]["id"] != team_id for e in body["form"])


async def test_head_to_head_is_symmetric(client: AsyncClient) -> None:
    team_id = await _football_team_id(client)
    analysis = (await client.get(f"{V1}/teams/{team_id}/analysis")).json()
    opponent_id = analysis["form"][0]["opponent"]["id"]

    ab = (await client.get(f"{V1}/teams/{team_id}/h2h/{opponent_id}")).json()
    ba = (await client.get(f"{V1}/teams/{opponent_id}/h2h/{team_id}")).json()
    assert ab["summary"]["played"] >= 1
    assert ab["summary"]["won"] == ba["summary"]["lost"]
    assert ab["summary"]["scored"] == ba["summary"]["conceded"]
    for match in ab["matches"]:
        ids = {p["team"]["id"] for p in match["participants"]}
        assert ids == {team_id, opponent_id}


async def test_analysis_unknown_team_is_404(client: AsyncClient) -> None:
    assert (await client.get(f"{V1}/teams/999999/analysis")).status_code == 404
    team_id = await _football_team_id(client)
    assert (await client.get(f"{V1}/teams/{team_id}/h2h/999999")).status_code == 404


async def test_analysis_rejects_bad_form_size(client: AsyncClient) -> None:
    team_id = await _football_team_id(client)
    assert (await client.get(f"{V1}/teams/{team_id}/analysis?last=500")).status_code == 422
