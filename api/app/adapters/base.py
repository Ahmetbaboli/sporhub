from abc import ABC, abstractmethod

from app.adapters.dto import CompetitionDTO, EventDTO, StandingDTO, TeamDTO


class BaseAdapter(ABC):
    """Fetches data from one external source and returns common DTOs.

    Adapters only read and normalize; persistence lives in services/sync_service.py.
    """

    sport_slug: str
    sport_name: str
    source: str
    # External competition ids the scheduler/admin sync should import by default.
    default_competitions: tuple[str, ...] = ()

    @abstractmethod
    async def fetch_competitions(self) -> list[CompetitionDTO]: ...

    @abstractmethod
    async def fetch_events(self, competition_ext_id: str, season: str) -> list[EventDTO]: ...

    @abstractmethod
    async def fetch_standings(self, competition_ext_id: str, season: str) -> list[StandingDTO]: ...

    @abstractmethod
    async def fetch_teams(self, competition_ext_id: str, season: str) -> list[TeamDTO]: ...

    async def aclose(self) -> None:  # noqa: B027 - optional hook
        """Release network resources."""
