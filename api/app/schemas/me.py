from pydantic import BaseModel, ConfigDict, Field

from app.schemas.api import CompetitionOut, EventOut, PlayerOut, SeasonOut, StandingOut, TeamOut


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str | None = None
    avatar_url: str | None = None


class FavoriteIds(BaseModel):
    """Compact form for rendering star buttons."""

    teams: list[int] = Field(default_factory=list)
    players: list[int] = Field(default_factory=list)
    competitions: list[int] = Field(default_factory=list)


class Favorites(BaseModel):
    teams: list[TeamOut] = Field(default_factory=list)
    players: list[PlayerOut] = Field(default_factory=list)
    competitions: list[CompetitionOut] = Field(default_factory=list)


class TeamActivity(BaseModel):
    team: TeamOut
    recent: list[EventOut]
    upcoming: list[EventOut]


class CompetitionPlace(BaseModel):
    competition: CompetitionOut
    season: SeasonOut | None = None
    table: list[StandingOut]  # top of the table
    mine: list[StandingOut]  # rows of the user's favorite teams/players in this competition


class Dashboard(BaseModel):
    teams: list[TeamActivity]
    competitions: list[CompetitionPlace]
