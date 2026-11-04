"""Elo ratings and a Monte Carlo season simulation. Pure functions: no database, no I/O.

Elo follows the World Football Elo idea: after each match the winner takes rating points from
the loser, more for an upset and for a wide margin; the home side gets a fixed bonus. Match
odds come from the Elo gap; the draw chance is highest between equals. The rest of the season
is then played many times with those odds and every finishing place is counted.
"""

import math
import random
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

INITIAL_ELO = 1500.0
K_FACTOR = 30.0
HOME_ADVANTAGE = 60.0
ELO_SCALE = 400.0
# Draw chance: DRAW_PEAK between equal sides, falling with the gap, never below DRAW_FLOOR.
DRAW_PEAK = 0.28
DRAW_SLOPE = 0.4
DRAW_FLOOR = 0.05
MIN_OUTCOME = 0.01
# Winning margin in a simulated match: 1 goal, then each extra goal with this chance (max 5).
EXTRA_GOAL_CHANCE = 0.45
MAX_MARGIN = 5
WIN_POINTS, DRAW_POINTS = 3, 1
TWO_GOALS, TWO_GOAL_MULTIPLIER = 2, 1.5
BIG_MARGIN_BASE, BIG_MARGIN_DIVISOR = 11, 8


@dataclass(frozen=True)
class Played:
    home: int
    away: int
    home_goals: int
    away_goals: int


@dataclass(frozen=True)
class Fixture:
    home: int
    away: int


@dataclass
class Row:
    points: int = 0
    goal_difference: int = 0
    played: int = 0


def margin_multiplier(goal_difference: int) -> float:
    """World Football Elo: x1 for one goal, x1.5 for two, (11 + N) / 8 for N >= 3."""
    gd = abs(goal_difference)
    if gd <= 1:
        return 1.0
    if gd == TWO_GOALS:
        return TWO_GOAL_MULTIPLIER
    return (BIG_MARGIN_BASE + gd) / BIG_MARGIN_DIVISOR


def expected_home(home_elo: float, away_elo: float) -> float:
    """Home side's expected score (win = 1, draw = 0.5) including home advantage."""
    return 1 / (1 + 10 ** (-(home_elo + HOME_ADVANTAGE - away_elo) / ELO_SCALE))


def elo_ratings(teams: Iterable[int], played: Sequence[Played]) -> dict[int, float]:
    """`played` in kick-off order."""
    ratings = dict.fromkeys(teams, INITIAL_ELO)
    for m in played:
        home, away = (
            ratings.setdefault(m.home, INITIAL_ELO),
            ratings.setdefault(m.away, INITIAL_ELO),
        )
        diff = m.home_goals - m.away_goals
        result = 1.0 if diff > 0 else 0.5 if diff == 0 else 0.0
        change = K_FACTOR * margin_multiplier(diff) * (result - expected_home(home, away))
        ratings[m.home] = home + change
        ratings[m.away] = away - change
    return ratings


def outcome_probabilities(home_elo: float, away_elo: float) -> tuple[float, float, float]:
    """(home win, draw, away win), summing to 1."""
    e = expected_home(home_elo, away_elo)
    draw = max(DRAW_FLOOR, DRAW_PEAK - DRAW_SLOPE * abs(e - 0.5))
    home = max(MIN_OUTCOME, e - draw / 2)
    away = max(MIN_OUTCOME, 1 - e - draw / 2)
    total = home + draw + away
    return home / total, draw / total, away / total


def table(teams: Iterable[int], played: Sequence[Played]) -> dict[int, Row]:
    rows = {t: Row() for t in teams}
    for m in played:
        h, a = rows.setdefault(m.home, Row()), rows.setdefault(m.away, Row())
        diff = m.home_goals - m.away_goals
        h.played += 1
        a.played += 1
        h.goal_difference += diff
        a.goal_difference -= diff
        if diff > 0:
            h.points += WIN_POINTS
        elif diff < 0:
            a.points += WIN_POINTS
        else:
            h.points += DRAW_POINTS
            a.points += DRAW_POINTS
    return rows


@dataclass(frozen=True)
class Simulation:
    runs: int
    # position_counts[team][i] = runs finishing (i + 1)th
    position_counts: dict[int, list[int]]
    points_total: dict[int, int]


def _margin(rng: random.Random) -> int:
    margin = 1
    while margin < MAX_MARGIN and rng.random() < EXTRA_GOAL_CHANCE:
        margin += 1
    return margin


def simulate(
    rows: dict[int, Row],
    fixtures: Sequence[Fixture],
    ratings: dict[int, float],
    runs: int,
    rng: random.Random,
) -> Simulation:
    """Plays `fixtures` `runs` times on top of the current table.

    Ranking: points, then goal difference, then a coin toss (head-to-head rules differ by
    league and the simulated scores are too rough to apply them).
    """
    teams = list(rows)
    odds = []
    for f in fixtures:
        home, draw, _ = outcome_probabilities(ratings[f.home], ratings[f.away])
        odds.append((f.home, f.away, home, home + draw))
    counts = {t: [0] * len(teams) for t in teams}
    points_total = dict.fromkeys(teams, 0)
    for _ in range(runs):
        points = {t: rows[t].points for t in teams}
        gd = {t: rows[t].goal_difference for t in teams}
        for home, away, p_home, p_not_away in odds:
            roll = rng.random()
            if roll < p_home:
                points[home] += WIN_POINTS
                m = _margin(rng)
                gd[home] += m
                gd[away] -= m
            elif roll < p_not_away:
                points[home] += DRAW_POINTS
                points[away] += DRAW_POINTS
            else:
                points[away] += WIN_POINTS
                m = _margin(rng)
                gd[away] += m
                gd[home] -= m
        order = sorted(teams, key=lambda t: (points[t], gd[t], rng.random()), reverse=True)
        for place, t in enumerate(order):
            counts[t][place] += 1
            points_total[t] += points[t]
    return Simulation(runs=runs, position_counts=counts, points_total=points_total)


def equal_fixture_counts(teams: Iterable[int], matches: Iterable[tuple[int, int]]) -> bool:
    """League-table formats give every team the same number of matches (cups do not)."""
    counts = dict.fromkeys(teams, 0)
    for home, away in matches:
        counts[home] = counts.get(home, 0) + 1
        counts[away] = counts.get(away, 0) + 1
    return len(set(counts.values())) == 1 if counts else False


def share(count: int, runs: int) -> float:
    return round(count / runs, 4) if runs else 0.0


def rounded(value: float, digits: int = 1) -> float:
    return math.floor(value * 10**digits + 0.5) / 10**digits
