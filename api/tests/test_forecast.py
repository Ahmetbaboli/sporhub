import random
from types import SimpleNamespace
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core import cache
from app.services import forecast_model as fm
from app.services.forecast_service import spots

V1 = "/api/v1"


def test_margin_multiplier_follows_world_football_elo() -> None:
    assert fm.margin_multiplier(0) == fm.margin_multiplier(1) == 1.0
    assert fm.margin_multiplier(-2) == 1.5
    assert fm.margin_multiplier(5) == 2.0  # (11 + 5) / 8


def test_odds_favour_home_and_the_stronger_side() -> None:
    home, draw, away = fm.outcome_probabilities(1500, 1500)
    assert home + draw + away == pytest.approx(1)
    assert home > away  # home advantage only
    assert draw == fm.outcome_probabilities(1500, 1500)[1] > fm.outcome_probabilities(1700, 1500)[1]
    strong = fm.outcome_probabilities(1800, 1400)
    assert strong[0] > 0.7 and strong[1] < draw  # big gap: fewer draws
    assert min(fm.outcome_probabilities(1000, 2500)) >= fm.MIN_OUTCOME / 1.1


def test_elo_moves_points_from_loser_to_winner() -> None:
    ratings = fm.elo_ratings([1, 2], [fm.Played(1, 2, 3, 0)])
    assert ratings[1] > fm.INITIAL_ELO > ratings[2]
    assert ratings[1] + ratings[2] == pytest.approx(2 * fm.INITIAL_ELO)
    # Winning 1-0 away is worth more than winning 1-0 at home (the home side was expected to).
    home_win = fm.elo_ratings([1, 2], [fm.Played(1, 2, 1, 0)])
    away_win = fm.elo_ratings([1, 2], [fm.Played(1, 2, 0, 1)])
    assert away_win[2] - fm.INITIAL_ELO > home_win[1] - fm.INITIAL_ELO


def test_table_counts_points_and_goal_difference() -> None:
    rows = fm.table([1, 2, 3], [fm.Played(1, 2, 2, 0), fm.Played(2, 3, 1, 1)])
    assert (rows[1].points, rows[2].points, rows[3].points) == (3, 1, 1)
    assert rows[2].goal_difference == -2 and rows[2].played == 2


def test_simulation_is_deterministic_and_counts_every_run() -> None:
    teams = [1, 2, 3, 4]
    rows = fm.table(teams, [])
    rows[1].points = 30  # out of reach with two games left each
    fixtures = [fm.Fixture(1, 2), fm.Fixture(3, 4), fm.Fixture(2, 3), fm.Fixture(4, 1)]
    ratings = dict.fromkeys(teams, fm.INITIAL_ELO)
    a = fm.simulate(rows, fixtures, ratings, 500, random.Random("x"))
    b = fm.simulate(rows, fixtures, ratings, 500, random.Random("x"))
    assert a == b
    assert a.position_counts[1][0] == 500
    assert all(sum(c) == 500 for c in a.position_counts.values())
    assert all(sum(c[i] for c in a.position_counts.values()) == 500 for i in range(4))


def test_cups_are_not_league_tables() -> None:
    assert fm.equal_fixture_counts([1, 2, 3], [(1, 2), (2, 3), (3, 1)])
    assert not fm.equal_fixture_counts([1, 2, 3], [(1, 2), (1, 3)])
    assert not fm.equal_fixture_counts([], [])


def _standing(zone: str | None) -> Any:
    return SimpleNamespace(extra={"zone": zone})


def test_spots_read_the_provider_zones_or_fall_back() -> None:
    table = [_standing("Champions League"), _standing("Europa League qualifying")]
    table += [_standing(None)] * 3 + [_standing("Relegated")] * 2
    assert spots("super-lig", table, 7) == (2, "europe", 2)
    assert spots("premier-league", [], 20) == (4, "top", 3)
    assert spots("uefa-champions-league", [], 36) == (8, "top", None)


@pytest.fixture(autouse=True)
async def _data(seeded: async_sessionmaker) -> None:
    await cache.get_cache().clear()


async def test_season_forecast_endpoint(client: AsyncClient) -> None:
    r = await client.get(f"{V1}/competitions/premier-league/forecast")
    assert r.status_code == 200
    body = r.json()
    assert body["available"] and body["simulations"] == 10_000
    assert (body["played"], body["remaining"]) == (84, 36)
    assert (body["top_spots"], body["relegation_spots"]) == (4, 3)
    teams = body["teams"]
    assert len(teams) == 20
    assert sum(t["title"] for t in teams) == pytest.approx(1, abs=1e-3)
    assert sum(t["relegation"] for t in teams) == pytest.approx(3, abs=1e-3)
    for t in teams:
        assert sum(t["positions"]) == pytest.approx(1, abs=1e-3)
        assert t["expected_points"] >= t["points"]
    expected = [t["expected_points"] for t in teams]
    assert expected == sorted(expected, reverse=True)
    # Same results, same numbers (seeded), served again from the cache.
    assert (await client.get(f"{V1}/competitions/premier-league/forecast")).json() == body


async def test_forecast_unknown_league_is_404(client: AsyncClient) -> None:
    assert (await client.get(f"{V1}/competitions/nope/forecast")).status_code == 404


async def test_match_forecast(client: AsyncClient) -> None:
    events = (
        await client.get(
            f"{V1}/competitions/premier-league/events",
            params={"status": "scheduled", "page_size": 1},
        )
    ).json()["items"]
    upcoming = events[0]["id"]
    odds = (await client.get(f"{V1}/events/{upcoming}/forecast")).json()
    assert odds["available"]
    assert odds["home"] + odds["draw"] + odds["away"] == pytest.approx(1, abs=1e-3)
    finished = (
        await client.get(
            f"{V1}/competitions/premier-league/events",
            params={"status": "finished", "page_size": 1},
        )
    ).json()["items"][0]["id"]
    done = (await client.get(f"{V1}/events/{finished}/forecast")).json()
    assert (done["available"], done["reason"]) == (False, "finished")
    assert (await client.get(f"{V1}/events/999999/forecast")).status_code == 404
