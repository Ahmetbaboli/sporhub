"""Season forecast (Elo + Monte Carlo) and single-match win probabilities."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.api import CompetitionOut, TeamOut

ForecastReason = Literal["unsupported", "not_started", "finished"]


class TeamForecast(BaseModel):
    team: TeamOut
    elo: float
    played: int
    points: int
    goal_difference: int
    expected_points: float
    # positions[i] = chance of finishing (i + 1)th, 0..1; sums to 1.
    positions: list[float]
    title: float
    top: float
    relegation: float | None = None


class SeasonForecast(BaseModel):
    competition: CompetitionOut
    season: str | None = None
    available: bool
    reason: ForecastReason | None = None
    simulations: int = 0
    played: int = 0
    remaining: int = 0
    # How many places count as "top" (European places / last-16 places) and how many go down.
    top_spots: int = 0
    top_kind: Literal["europe", "top"] = "top"
    relegation_spots: int | None = None
    teams: list[TeamForecast] = Field(default_factory=list)
    generated_at: datetime | None = None


class MatchForecast(BaseModel):
    event_id: int
    available: bool
    reason: ForecastReason | None = None
    home: float | None = None
    draw: float | None = None
    away: float | None = None
    home_elo: float | None = None
    away_elo: float | None = None
