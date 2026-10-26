"""Common DTOs every adapter normalizes into. Adapters never touch the database."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

EventKind = Literal["match", "race", "session"]
EventStatus = Literal["scheduled", "live", "finished", "postponed", "cancelled"]
Side = Literal["home", "away"]


class TeamRef(BaseModel):
    external_id: str
    name: str
    short_name: str | None = None
    logo_url: str | None = None


class PlayerDTO(BaseModel):
    external_id: str
    name: str
    position: str | None = None
    nationality: str | None = None
    extra: dict = Field(default_factory=dict)


class TeamDTO(TeamRef):
    country: str | None = None
    squad: list[PlayerDTO] = Field(default_factory=list)


class CompetitionDTO(BaseModel):
    external_id: str
    name: str
    country: str | None = None
    logo_url: str | None = None
    # Value passed back to fetch_* as `season` (e.g. "2026"), and its display label.
    season_key: str | None = None
    season_label: str | None = None
    season_start: date | None = None
    season_end: date | None = None


class ParticipantDTO(BaseModel):
    team: TeamRef | None = None
    player_external_id: str | None = None
    side: Side | None = None
    score: int | None = None
    position: int | None = None
    points: float | None = None
    extra: dict = Field(default_factory=dict)


class EventDTO(BaseModel):
    external_id: str
    kind: EventKind
    name: str | None = None
    start_time: datetime
    status: EventStatus
    venue: str | None = None
    round: str | None = None
    participants: list[ParticipantDTO] = Field(default_factory=list)
    extra: dict = Field(default_factory=dict)


class StandingDTO(BaseModel):
    team: TeamRef | None = None
    player_external_id: str | None = None
    position: int
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    points: float = 0
    extra: dict = Field(default_factory=dict)
