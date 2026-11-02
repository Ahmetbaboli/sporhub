from pydantic import BaseModel, Field

from app.schemas.api import EventOut, PlayerOut, SeasonOut, StandingOut, TeamOut


class LeaderRow(BaseModel):
    rank: int
    player: PlayerOut | None = None
    team: TeamOut | None = None
    value: float
    played: int | None = None  # sample size behind a rate (matches/races)


class LeaderCategory(BaseModel):
    """`key` is a stable name the UI translates (goals, best_attack, wins, ...)."""

    key: str
    subject: str  # "player" | "team"
    rows: list[LeaderRow]


class MatchSummary(BaseModel):
    """Season-wide numbers for two-sided match sports."""

    played: int = 0
    total_scored: int = 0
    avg_per_match: float = 0.0
    home_win_pct: float = 0.0
    draw_pct: float = 0.0
    away_win_pct: float = 0.0
    biggest_win: EventOut | None = None
    highest_scoring: EventOut | None = None


class RaceSummary(BaseModel):
    completed: int = 0
    scheduled: int = 0
    distinct_winners: int = 0
    pole_to_win: int = 0  # races won from pole position


class SeasonHistoryRow(BaseModel):
    season: SeasonOut
    leader: StandingOut | None = None  # champion, or current leader when unfinished


class CompetitionStats(BaseModel):
    season: SeasonOut | None = None
    matches: MatchSummary | None = None
    races: RaceSummary | None = None
    leaders: list[LeaderCategory] = Field(default_factory=list)
    history: list[SeasonHistoryRow] = Field(default_factory=list)
