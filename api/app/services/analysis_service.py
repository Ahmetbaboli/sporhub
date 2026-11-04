"""Team form, home/away splits and head-to-head, computed from finished two-sided matches.

Race sports (F1) have no sides or opponents, so their analysis is simply empty.
"""

from collections import Counter
from collections.abc import Iterable, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cached
from app.core.errors import NotFoundError
from app.models import Event, Season, Team
from app.repositories import queries
from app.schemas.analysis import FormEntry, HeadToHead, SplitStats, TeamAnalysis
from app.services.read_service import event_out, team_out

DEFAULT_FORM_SIZE = 10
MAX_ANALYSIS_EVENTS = 200
DEFAULT_H2H_SIZE = 10
DECIMALS = 2


def entry_for(event: Event, team_id: int) -> FormEntry | None:
    """The match from `team_id`'s side, or None if it is not a scored two-team match."""
    if event.kind != "match" or event.status != "finished":
        return None
    mine = next((p for p in event.participants if p.team_id == team_id), None)
    other = next((p for p in event.participants if p.team_id not in (None, team_id)), None)
    if mine is None or other is None or other.team is None:
        return None
    if mine.score is None or other.score is None or mine.side not in ("home", "away"):
        return None
    result = "W" if mine.score > other.score else "L" if mine.score < other.score else "D"
    return FormEntry(
        event_id=event.id,
        start_time=event.start_time,
        competition=event.season.competition.name,
        side=mine.side,
        opponent=team_out(other.team),
        scored=mine.score,
        conceded=other.score,
        result=result,
    )


def summarize(entries: Iterable[FormEntry]) -> SplitStats:
    items = list(entries)
    played = len(items)
    if played == 0:
        return SplitStats()
    won = sum(e.result == "W" for e in items)
    scored = sum(e.scored for e in items)
    conceded = sum(e.conceded for e in items)
    return SplitStats(
        played=played,
        won=won,
        drawn=sum(e.result == "D" for e in items),
        lost=sum(e.result == "L" for e in items),
        scored=scored,
        conceded=conceded,
        win_pct=round(won / played, DECIMALS),
        avg_scored=round(scored / played, DECIMALS),
        avg_conceded=round(conceded / played, DECIMALS),
        clean_sheets=sum(e.conceded == 0 for e in items),
    )


def current_streak(entries: Sequence[FormEntry]) -> str | None:
    """Entries are most recent first; "W3" means the last three were wins."""
    if not entries:
        return None
    first = entries[0].result
    length = next((i for i, e in enumerate(entries) if e.result != first), len(entries))
    return f"{first}{length}"


def _margin(entry: FormEntry) -> int:
    return entry.scored - entry.conceded


def main_season(pairs: Sequence[tuple[Event, FormEntry]]) -> Season:
    """The season the season panel describes: the team's busiest current one.

    A club plays its league and a cup or European competition at once; the most recent match
    may be a Champions League night, but the league (more matches) is what the season is about.
    Only current seasons compete, so an old full season never beats a young one; when the source
    marks none current, the latest match's season is used. Ties go to the most recent.
    """
    seasons = [event.season for event, _ in pairs]
    current = [s for s in seasons if s.is_current] or [seasons[0]]
    counts = Counter(s.id for s in current)
    # `seasons` is newest first, so max() keeps the most recent on equal counts.
    return max({s.id: s for s in current}.values(), key=lambda s: counts[s.id])


def analyse(team: Team, events: Sequence[Event], form_size: int) -> TeamAnalysis:
    """`events` are finished events of the team, most recent first."""
    pairs = [(e, entry) for e in events if (entry := entry_for(e, team.id)) is not None]
    if not pairs:
        return TeamAnalysis(team=team_out(team))
    main = main_season(pairs)
    season = [entry for event, entry in pairs if event.season_id == main.id]
    form = [entry for _, entry in pairs[:form_size]]
    wins = [e for e in season if e.result == "W"]
    losses = [e for e in season if e.result == "L"]
    return TeamAnalysis(
        team=team_out(team),
        season=main.year_label,
        form=form,
        form_stats=summarize(form),
        streak=current_streak(form),
        overall=summarize(season),
        home=summarize(e for e in season if e.side == "home"),
        away=summarize(e for e in season if e.side == "away"),
        biggest_win=max(wins, key=_margin) if wins else None,
        biggest_loss=min(losses, key=_margin) if losses else None,
    )


async def _require_team(session: AsyncSession, team_id: int) -> Team:
    team = await queries.get_team(session, team_id)
    if team is None:
        raise NotFoundError("Takım")
    return team


async def get_team_analysis(
    session: AsyncSession, team_id: int, form_size: int = DEFAULT_FORM_SIZE
) -> TeamAnalysis:
    async def load() -> TeamAnalysis:
        team = await _require_team(session, team_id)
        events = await queries.list_finished_matches(session, team_id, MAX_ANALYSIS_EVENTS)
        return analyse(team, events, form_size)

    return await cached(f"analysis:{team_id}:{form_size}", TeamAnalysis, load)


async def get_head_to_head(
    session: AsyncSession, team_id: int, opponent_id: int, limit: int = DEFAULT_H2H_SIZE
) -> HeadToHead:
    async def load() -> HeadToHead:
        team = await _require_team(session, team_id)
        opponent = await _require_team(session, opponent_id)
        events = await queries.list_finished_matches(session, team_id, limit, opponent_id)
        entries = [entry for e in events if (entry := entry_for(e, team_id)) is not None]
        return HeadToHead(
            team=team_out(team),
            opponent=team_out(opponent),
            summary=summarize(entries),
            matches=[event_out(e) for e in events],
        )

    return await cached(f"h2h:{team_id}:{opponent_id}:{limit}", HeadToHead, load)
