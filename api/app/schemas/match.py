from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.adapters.dto import IncidentDTO, LineupDTO, MatchStatDTO

# Why a match has no details: the source never offers them, the match is too far away to
# have a lineup yet, or the provider could not be reached right now.
UnavailableReason = Literal["unsupported", "not_started", "unavailable"]


class MatchDetailsOut(BaseModel):
    event_id: int
    available: bool
    reason: UnavailableReason | None = None
    source: str | None = None
    lineups: list[LineupDTO] = Field(default_factory=list)
    incidents: list[IncidentDTO] = Field(default_factory=list)
    stats: list[MatchStatDTO] = Field(default_factory=list)
    attendance: int | None = None
    fetched_at: datetime | None = None
