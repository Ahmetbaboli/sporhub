"""Competition statistics: season summary, leader boards and season history.

Everything except player stat sheets (goals/assists from the source) is derived from the
events and standings already stored, so every sport gets numbers without new API calls.
"""

from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cached
from app.models import Event, EventParticipant, Player, PlayerStat, Season, Standing, Team
from app.repositories import queries
from app.schemas.api import SeasonOut
from app.schemas.stats import (
    CompetitionStats,
    LeaderCategory,
    LeaderRow,
    MatchSummary,
    RaceSummary,
    SeasonHistoryRow,
)
from app.services.read_service import (
    _require_competition,
    event_out,
    player_out,
    standing_out,
    team_out,
)

PLAYER_LEADERS = 10
TEAM_LEADERS = 5
DECIMALS = 2
PODIUM = 3
# Rates need a sample: at least this share of the busiest team's/driver's games.
MIN_SAMPLE_SHARE = 0.5
# Stat-sheet keys shown as leader boards, in display order.
STAT_SHEET_KEYS = ("goals", "assists", "penalties")
FINISHED = "finished"


def _rate(value: float, played: int) -> float:
    return round(value / played, DECIMALS) if played else 0.0


def ranked(
    items: Iterable[tuple[Player | None, Team | None, float, int | None]],
    limit: int,
    ascending: bool = False,
) -> list[LeaderRow]:
    """Sorted rows with competition ranking (ties share a rank: 1, 1, 3)."""
    ordered = sorted(items, key=lambda i: i[2] if ascending else -i[2])[:limit]
    rows: list[LeaderRow] = []
    for index, (player, team, value, played) in enumerate(ordered):
        rank = rows[-1].rank if rows and rows[-1].value == value else index + 1
        rows.append(
            LeaderRow(
                rank=rank,
                player=player_out(player) if player else None,
                team=team_out(team) if team else None,
                value=value,
                played=played,
            )
        )
    return rows


# ---- two-sided matches ------------------------------------------------------------------


def _scored_pair(event: Event) -> tuple[EventParticipant, EventParticipant] | None:
    if event.kind != "match" or event.status != FINISHED:
        return None
    home = next((p for p in event.participants if p.side == "home"), None)
    away = next((p for p in event.participants if p.side == "away"), None)
    if not home or not away or home.score is None or away.score is None:
        return None
    if home.team is None or away.team is None:
        return None
    return home, away


def match_summary(events: Sequence[Event]) -> MatchSummary | None:
    pairs = [(e, pair) for e in events if (pair := _scored_pair(e))]
    if not pairs:
        return None
    played = len(pairs)
    total = sum(h.score + a.score for _, (h, a) in pairs)
    home_wins = sum(h.score > a.score for _, (h, a) in pairs)
    draws = sum(h.score == a.score for _, (h, a) in pairs)
    biggest = max(pairs, key=lambda x: abs(x[1][0].score - x[1][1].score))[0]
    highest = max(pairs, key=lambda x: x[1][0].score + x[1][1].score)[0]
    return MatchSummary(
        played=played,
        total_scored=total,
        avg_per_match=_rate(total, played),
        home_win_pct=_rate(home_wins, played),
        draw_pct=_rate(draws, played),
        away_win_pct=_rate(played - home_wins - draws, played),
        biggest_win=event_out(biggest),
        highest_scoring=event_out(highest),
    )


@dataclass
class _TeamTotals:
    team: Team
    played: int = 0
    scored: int = 0
    conceded: int = 0
    clean_sheets: int = 0
    home_played: int = 0
    home_won: int = 0
    away_played: int = 0
    away_won: int = 0


def _team_totals(events: Sequence[Event]) -> list[_TeamTotals]:
    totals: dict[int, _TeamTotals] = {}
    for event in events:
        pair = _scored_pair(event)
        if not pair:
            continue
        for mine, other in (pair, pair[::-1]):
            t = totals.setdefault(mine.team_id, _TeamTotals(team=mine.team))
            t.played += 1
            t.scored += mine.score
            t.conceded += other.score
            t.clean_sheets += other.score == 0
            won = mine.score > other.score
            if mine.side == "home":
                t.home_played += 1
                t.home_won += won
            else:
                t.away_played += 1
                t.away_won += won
    return list(totals.values())


def team_leaders(events: Sequence[Event]) -> list[LeaderCategory]:
    totals = _team_totals(events)
    if not totals:
        return []
    min_games = max(1, round(max(t.played for t in totals) * MIN_SAMPLE_SHARE))
    regular = [t for t in totals if t.played >= min_games]
    min_side = max(1, min_games // 2)
    boards: list[tuple[str, list[LeaderRow]]] = [
        (
            "best_attack",
            ranked(
                ((None, t.team, _rate(t.scored, t.played), t.played) for t in regular), TEAM_LEADERS
            ),
        ),
        (
            "best_defence",
            ranked(
                ((None, t.team, _rate(t.conceded, t.played), t.played) for t in regular),
                TEAM_LEADERS,
                ascending=True,
            ),
        ),
        (
            "clean_sheets",
            ranked(
                ((None, t.team, float(t.clean_sheets), t.played) for t in totals if t.clean_sheets),
                TEAM_LEADERS,
            ),
        ),
        (
            "home_win_pct",
            ranked(
                (
                    (None, t.team, _rate(t.home_won, t.home_played), t.home_played)
                    for t in totals
                    if t.home_played >= min_side
                ),
                TEAM_LEADERS,
            ),
        ),
        (
            "away_win_pct",
            ranked(
                (
                    (None, t.team, _rate(t.away_won, t.away_played), t.away_played)
                    for t in totals
                    if t.away_played >= min_side
                ),
                TEAM_LEADERS,
            ),
        ),
    ]
    return [LeaderCategory(key=k, subject="team", rows=rows) for k, rows in boards if rows]


def stat_sheet_leaders(stats: Sequence[PlayerStat]) -> list[LeaderCategory]:
    boards = []
    for key in STAT_SHEET_KEYS:
        items = [
            (s.player, s.team, float(s.stats[key]), _played(s)) for s in stats if s.stats.get(key)
        ]
        if items:
            boards.append(
                LeaderCategory(key=key, subject="player", rows=ranked(items, PLAYER_LEADERS))
            )
    return boards


def _played(stat: PlayerStat) -> int | None:
    value = stat.stats.get("played")
    return int(value) if value is not None else None


# ---- races ---------------------------------------------------------------------------------


def _race_results(events: Sequence[Event]) -> list[Event]:
    return [
        e
        for e in events
        if e.kind == "race" and e.status == FINISHED and any(p.player_id for p in e.participants)
    ]


def race_summary(events: Sequence[Event]) -> RaceSummary | None:
    races = [e for e in events if e.kind == "race"]
    if not races:
        return None
    done = _race_results(events)
    winners = [p for e in done for p in e.participants if p.position == 1 and p.player_id]
    return RaceSummary(
        completed=len(done),
        scheduled=len(races) - len(done),
        distinct_winners=len({w.player_id for w in winners}),
        pole_to_win=sum((w.extra or {}).get("grid") == 1 for w in winners),
    )


def race_leaders(events: Sequence[Event]) -> list[LeaderCategory]:
    rows: dict[int, list[EventParticipant]] = defaultdict(list)
    for event in _race_results(events):
        for p in event.participants:
            if p.player_id and p.player:
                rows[p.player_id].append(p)
    if not rows:
        return []

    def board(
        key: str, value: Callable[[list[EventParticipant]], float], ascending: bool = False
    ) -> LeaderCategory | None:
        items = [
            (results[0].player, results[-1].team, value(results), len(results))
            for results in rows.values()
        ]
        items = [i for i in items if ascending or i[2] > 0]
        if ascending:
            min_races = max(1, round(max(len(r) for r in rows.values()) * MIN_SAMPLE_SHARE))
            items = [i for i in items if i[3] >= min_races]
        ranked_rows = ranked(items, PLAYER_LEADERS, ascending)
        return LeaderCategory(key=key, subject="player", rows=ranked_rows) if ranked_rows else None

    def finishes(results: list[EventParticipant]) -> float:
        positions = [r.position for r in results if r.position]
        return round(sum(positions) / len(positions), DECIMALS) if positions else 99.0

    boards = [
        board("wins", lambda r: float(sum(p.position == 1 for p in r))),
        board("podiums", lambda r: float(sum((p.position or 99) <= PODIUM for p in r))),
        board("poles", lambda r: float(sum((p.extra or {}).get("grid") == 1 for p in r))),
        board(
            "fastest_laps",
            lambda r: float(sum((p.extra or {}).get("fastest_lap_rank") == 1 for p in r)),
        ),
        board("avg_finish", finishes, ascending=True),
    ]
    return [b for b in boards if b]


# ---- history ---------------------------------------------------------------------------------


def season_leader(rows: Sequence[Standing]) -> Standing | None:
    """Champion/leader: the best driver row when drivers are ranked, else the best team."""
    if not rows:
        return None
    drivers = [r for r in rows if r.player_id is not None]
    pool = drivers or list(rows)
    return min(pool, key=lambda r: (r.position, -r.won, -r.points))


async def _history(session: AsyncSession, seasons: Sequence[Season]) -> list[SeasonHistoryRow]:
    history = []
    for season in seasons:
        leader = season_leader(await queries.list_standings(session, season.id))
        history.append(
            SeasonHistoryRow(
                season=SeasonOut.model_validate(season),
                leader=standing_out(leader) if leader else None,
            )
        )
    return history


async def get_competition_stats(session: AsyncSession, ref: str) -> CompetitionStats:
    async def load() -> CompetitionStats:
        comp = await _require_competition(session, ref)
        season = await queries.current_season(session, comp.id)
        history = await _history(session, await queries.list_seasons(session, comp.id))
        if season is None:
            return CompetitionStats(history=history)
        events = await queries.list_season_events(session, season.id)
        sheets = await queries.list_player_stats(session, season.id)
        return CompetitionStats(
            season=SeasonOut.model_validate(season),
            matches=match_summary(events),
            races=race_summary(events),
            leaders=stat_sheet_leaders(sheets) + race_leaders(events) + team_leaders(events),
            history=history,
        )

    return await cached(f"cstats:{ref}", CompetitionStats, load)
