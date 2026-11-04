"""Season forecast and match odds from our own results (no outside data).

See `forecast_model` for the maths. A forecast is cached per competition and per state of the
results: a new finished match changes the key, so it is recomputed on the next request.
"""

import asyncio
import random
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cached
from app.core.errors import NotFoundError
from app.models import Event, Season, Standing, Team
from app.repositories import queries
from app.schemas.forecast import MatchForecast, SeasonForecast, TeamForecast
from app.services import forecast_model as fm
from app.services.read_service import competition_out, team_out

SIMULATIONS = 10_000
FORECAST_TTL_SECONDS = 6 * 60 * 60
# Odds for a single match need a few results per side, or they are just the home bonus.
MIN_MATCHES_FOR_ODDS = 3
SUPPORTED_SPORT = "football"  # needs draws and a points table
REMAINING_STATUSES = ("scheduled", "live", "postponed")
DEFAULT_TOP_SPOTS = 4
# Direct relegation places when the provider's table carries no zones (play-off places are not
# counted). UEFA's league phase has none; it uses its top 8 (straight to the last 16) instead.
RELEGATION_SPOTS = {
    "premier-league": 3,
    "championship": 3,
    "primera-division": 3,
    "serie-a": 3,
    "bundesliga": 2,
    "ligue-1": 2,
    "eredivisie": 2,
    "primeira-liga": 2,
    "campeonato-brasileiro-serie-a": 4,
}
TOP_SPOTS = {"uefa-champions-league": 8}
RELEGATION_ZONES = ("relegat",)
EUROPEAN_ZONE = "league"  # "Champions League", "Europa League qualifying", ...


def _sides(event: Event) -> tuple[int, int, int | None, int | None] | None:
    home = next((p for p in event.participants if p.side == "home"), None)
    away = next((p for p in event.participants if p.side == "away"), None)
    if not home or not away or home.team_id is None or away.team_id is None:
        return None
    return home.team_id, away.team_id, home.score, away.score


def split_events(events: Sequence[Event]) -> tuple[list[fm.Played], list[fm.Fixture], int | None]:
    """(finished in kick-off order, still to play, id of the latest finished match)."""
    played: list[fm.Played] = []
    remaining: list[fm.Fixture] = []
    last_id: int | None = None
    for e in sorted(events, key=lambda e: (e.start_time, e.id)):
        sides = _sides(e) if e.kind == "match" else None
        if sides is None:
            continue
        home, away, hs, as_ = sides
        if e.status == "finished" and hs is not None and as_ is not None:
            played.append(fm.Played(home, away, hs, as_))
            last_id = e.id
        elif e.status in REMAINING_STATUSES:
            remaining.append(fm.Fixture(home, away))
    return played, remaining, last_id


def _zone_count(rows: Sequence[Standing], words: tuple[str, ...], top: bool) -> int:
    ordered = rows if top else list(reversed(rows))
    count = 0
    for row in ordered:
        zone = str((row.extra or {}).get("zone") or "").lower()
        if not any(w in zone for w in words):
            break
        count += 1
    return count


def spots(slug: str, standings: Sequence[Standing], team_count: int) -> tuple[int, str, int | None]:
    """(top places, "europe" | "top", relegation places or None)."""
    europe = _zone_count(standings, (EUROPEAN_ZONE,), top=True)
    relegation = _zone_count(standings, RELEGATION_ZONES, top=False) or RELEGATION_SPOTS.get(slug)
    if europe:
        return europe, "europe", relegation
    return min(TOP_SPOTS.get(slug, DEFAULT_TOP_SPOTS), team_count), "top", relegation


def _team_ids(played: Sequence[fm.Played], remaining: Sequence[fm.Fixture]) -> list[int]:
    ids = {t for m in played for t in (m.home, m.away)}
    ids |= {t for f in remaining for t in (f.home, f.away)}
    return sorted(ids)


def _supported(
    sport: str, teams: list[int], played: list[fm.Played], rest: list[fm.Fixture]
) -> bool:
    pairs = [(m.home, m.away) for m in played] + [(f.home, f.away) for f in rest]
    return sport == SUPPORTED_SPORT and fm.equal_fixture_counts(teams, pairs)


async def get_season_forecast(session: AsyncSession, ref: str) -> SeasonForecast:
    comp = await queries.get_competition(session, ref)
    if comp is None:
        raise NotFoundError("Lig")
    base = SeasonForecast(competition=competition_out(comp), available=False)
    season = await queries.current_season(session, comp.id)
    if season is None:
        return base.model_copy(update={"reason": "not_started"})
    events = await queries.list_season_events(session, season.id)
    played, remaining, last_id = split_events(events)
    teams = _team_ids(played, remaining)
    base = base.model_copy(
        update={"season": season.year_label, "played": len(played), "remaining": len(remaining)}
    )
    if not _supported(comp.sport.slug, teams, played, remaining):
        return base.model_copy(update={"reason": "unsupported"})
    if not played:
        return base.model_copy(update={"reason": "not_started"})
    if not remaining:
        return base.model_copy(update={"reason": "finished"})

    by_id = {p.team_id: p.team for e in events for p in e.participants if p.team is not None}

    async def load() -> SeasonForecast:
        standings = await queries.list_standings(session, season.id)
        return await _forecast(base, season, standings, by_id, teams, played, remaining)

    key = f"forecast:{comp.id}:{season.id}:{len(played)}:{last_id}"
    return await cached(key, SeasonForecast, load, ttl=FORECAST_TTL_SECONDS)


async def _forecast(
    base: SeasonForecast,
    season: Season,
    standings: Sequence[Standing],
    by_id: dict[int, Team],
    teams: list[int],
    played: list[fm.Played],
    remaining: list[fm.Fixture],
) -> SeasonForecast:
    ratings = fm.elo_ratings(teams, played)
    rows = fm.table(teams, played)
    # Seeded by the results so the same state always gives the same numbers.
    rng = random.Random(f"{season.id}:{len(played)}")
    sim = await asyncio.to_thread(fm.simulate, rows, remaining, ratings, SIMULATIONS, rng)
    top_spots, top_kind, relegation_spots = spots(base.competition.slug, standings, len(teams))
    out = []
    for team_id in teams:
        counts = sim.position_counts[team_id]
        out.append(
            TeamForecast(
                team=team_out(by_id[team_id]),
                elo=fm.rounded(ratings[team_id]),
                played=rows[team_id].played,
                points=rows[team_id].points,
                goal_difference=rows[team_id].goal_difference,
                expected_points=fm.rounded(sim.points_total[team_id] / sim.runs),
                positions=[fm.share(c, sim.runs) for c in counts],
                title=fm.share(counts[0], sim.runs),
                top=fm.share(sum(counts[:top_spots]), sim.runs),
                relegation=(
                    fm.share(sum(counts[len(counts) - relegation_spots :]), sim.runs)
                    if relegation_spots
                    else None
                ),
            )
        )
    out.sort(key=lambda t: (-t.expected_points, -t.points, t.team.name))
    return base.model_copy(
        update={
            "available": True,
            "simulations": sim.runs,
            "top_spots": top_spots,
            "top_kind": top_kind,
            "relegation_spots": relegation_spots,
            "teams": out,
            "generated_at": datetime.now(UTC),
        }
    )


async def get_match_forecast(session: AsyncSession, event_id: int) -> MatchForecast:
    event = await queries.get_event(session, event_id)
    if event is None:
        raise NotFoundError("Maç")
    base = MatchForecast(event_id=event_id, available=False)
    sides = _sides(event) if event.kind == "match" else None
    if event.status == "finished":
        return base.model_copy(update={"reason": "finished"})
    if sides is None or event.status not in REMAINING_STATUSES:
        return base.model_copy(update={"reason": "unsupported"})
    played, remaining, _ = split_events(await queries.list_season_events(session, event.season_id))
    teams = _team_ids(played, remaining)
    if not _supported(event.season.competition.sport.slug, teams, played, remaining):
        return base.model_copy(update={"reason": "unsupported"})
    home_id, away_id = sides[0], sides[1]
    rows = fm.table(teams, played)
    if min(rows[home_id].played, rows[away_id].played) < MIN_MATCHES_FOR_ODDS:
        return base.model_copy(update={"reason": "not_started"})
    ratings = fm.elo_ratings(teams, played)
    home, draw, away = fm.outcome_probabilities(ratings[home_id], ratings[away_id])
    return base.model_copy(
        update={
            "available": True,
            "home": round(home, 4),
            "draw": round(draw, 4),
            "away": round(away, 4),
            "home_elo": fm.rounded(ratings[home_id]),
            "away_elo": fm.rounded(ratings[away_id]),
        }
    )
