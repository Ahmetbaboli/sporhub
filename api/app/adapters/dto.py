"""Common DTOs every adapter normalizes into. Adapters never touch the database."""

import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

EventKind = Literal["match", "race", "session"]
EventStatus = Literal["scheduled", "live", "finished", "postponed", "cancelled"]
Side = Literal["home", "away"]


HEX_COLOR = re.compile(r"^#?([0-9a-fA-F]{6})$")


def hex_color(value: object) -> str | None:
    """'ffff00' / '#FFFF00' -> '#ffff00'; anything else -> None."""
    match = HEX_COLOR.match(value) if isinstance(value, str) else None
    return f"#{match.group(1).lower()}" if match else None


class TeamRef(BaseModel):
    external_id: str
    name: str
    short_name: str | None = None
    logo_url: str | None = None
    color: str | None = None
    alternate_color: str | None = None


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


class PlayerStatDTO(BaseModel):
    """Season totals of one player in one competition (e.g. a scorers list).

    `player` carries enough to create the player when the squad import did not include them.
    `stats` keys are sport-neutral names: goals, assists, penalties, played, ...
    """

    player: PlayerDTO
    team: TeamRef | None = None
    stats: dict[str, float] = Field(default_factory=dict)


IncidentKind = Literal[
    "goal", "own_goal", "penalty_goal", "yellow_card", "red_card", "substitution"
]


class LineupPlayerDTO(BaseModel):
    external_id: str | None = None
    name: str
    number: str | None = None
    position: str | None = None
    subbed_in: bool = False
    subbed_out: bool = False


class LineupDTO(BaseModel):
    side: Side
    formation: str | None = None
    starters: list[LineupPlayerDTO] = Field(default_factory=list)
    substitutes: list[LineupPlayerDTO] = Field(default_factory=list)


class IncidentDTO(BaseModel):
    """One key moment. For substitutions `player` comes on and `related_player` goes off."""

    minute: str
    kind: IncidentKind
    side: Side | None = None
    player: str | None = None
    related_player: str | None = None


class MatchStatDTO(BaseModel):
    """One team statistic, home and away; keys are sport-neutral (possession, shots, ...)."""

    key: str
    home: float | None = None
    away: float | None = None


class MatchDetailsDTO(BaseModel):
    lineups: list[LineupDTO] = Field(default_factory=list)
    incidents: list[IncidentDTO] = Field(default_factory=list)
    stats: list[MatchStatDTO] = Field(default_factory=list)
    attendance: int | None = None

    def is_empty(self) -> bool:
        return not (self.lineups or self.incidents or self.stats)
