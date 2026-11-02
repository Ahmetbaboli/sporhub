from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.api import EventOut, TeamOut

Result = Literal["W", "D", "L"]


class SplitStats(BaseModel):
    """Aggregates over a set of finished matches, from one team's point of view."""

    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    scored: int = 0
    conceded: int = 0
    win_pct: float = 0.0
    avg_scored: float = 0.0
    avg_conceded: float = 0.0
    clean_sheets: int = 0


class FormEntry(BaseModel):
    event_id: int
    start_time: datetime
    competition: str
    side: Literal["home", "away"]
    opponent: TeamOut
    scored: int
    conceded: int
    result: Result


class TeamAnalysis(BaseModel):
    team: TeamOut
    season: str | None = None
    form: list[FormEntry] = Field(default_factory=list)  # most recent first
    form_stats: SplitStats = Field(default_factory=SplitStats)
    streak: str | None = None  # "W3" = three wins in a row
    overall: SplitStats = Field(default_factory=SplitStats)  # whole season
    home: SplitStats = Field(default_factory=SplitStats)
    away: SplitStats = Field(default_factory=SplitStats)
    biggest_win: FormEntry | None = None
    biggest_loss: FormEntry | None = None


class HeadToHead(BaseModel):
    team: TeamOut
    opponent: TeamOut
    summary: SplitStats  # from `team`'s point of view
    matches: list[EventOut] = Field(default_factory=list)  # most recent first
