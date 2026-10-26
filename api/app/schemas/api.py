"""Pydantic response models for the public REST API."""

from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class SportOut(ORMModel):
    id: int
    slug: str
    name: str


class CompetitionOut(BaseModel):
    id: int
    slug: str
    name: str
    sport_slug: str
    country: str | None = None
    logo_url: str | None = None


class SeasonOut(ORMModel):
    id: int
    year_label: str
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool


class CompetitionDetail(CompetitionOut):
    current_season: SeasonOut | None = None


class TeamOut(BaseModel):
    id: int
    name: str
    short_name: str | None = None
    logo_url: str | None = None
    country: str | None = None
    sport_slug: str | None = None


class PlayerOut(BaseModel):
    id: int
    name: str
    position: str | None = None
    nationality: str | None = None
    team: TeamOut | None = None
    extra: dict = Field(default_factory=dict)


class ParticipantOut(BaseModel):
    team: TeamOut | None = None
    player: PlayerOut | None = None
    side: str | None = None
    score: int | None = None
    position: int | None = None
    points: float | None = None
    extra: dict = Field(default_factory=dict)


class EventOut(BaseModel):
    id: int
    kind: str
    name: str | None = None
    start_time: datetime
    status: str
    venue: str | None = None
    round: str | None = None
    competition: CompetitionOut
    season: str
    participants: list[ParticipantOut]
    extra: dict = Field(default_factory=dict)


class StandingOut(BaseModel):
    position: int
    team: TeamOut | None = None
    player: PlayerOut | None = None
    played: int
    won: int
    drawn: int
    lost: int
    points: float
    extra: dict = Field(default_factory=dict)


class TeamDetail(TeamOut):
    squad: list[PlayerOut] = Field(default_factory=list)


class SearchResults(BaseModel):
    query: str
    competitions: list[CompetitionOut]
    teams: list[TeamOut]
    players: list[PlayerOut]


class HealthOut(BaseModel):
    status: str
    version: str


class SyncAccepted(BaseModel):
    status: str
    adapter: str
