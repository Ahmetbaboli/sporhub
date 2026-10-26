"""football-data.org v4 adapter.

Docs: https://docs.football-data.org/general/v4/ — auth via `X-Auth-Token`,
free tier allows 10 requests/minute.
"""

from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx

from app.adapters.dto import (
    CompetitionDTO,
    EventDTO,
    EventStatus,
    ParticipantDTO,
    PlayerDTO,
    StandingDTO,
    TeamDTO,
    TeamRef,
)
from app.adapters.http_fixture import HttpFixtureAdapter
from app.core.config import Settings

BASE_URL = "https://api.football-data.org/v4"
# Free tier: 10 requests per minute -> one request every 6 s, plus a safety margin.
MIN_REQUEST_INTERVAL_SECONDS = 6.5
TOTAL_STANDING_TYPE = "TOTAL"

STATUS_MAP: dict[str, EventStatus] = {
    "SCHEDULED": "scheduled",
    "TIMED": "scheduled",
    "IN_PLAY": "live",
    "PAUSED": "live",
    "LIVE": "live",
    "FINISHED": "finished",
    "AWARDED": "finished",
    "POSTPONED": "postponed",
    "SUSPENDED": "postponed",
    "CANCELLED": "cancelled",
}


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def season_label(start_year: int) -> str:
    return f"{start_year}/{str(start_year + 1)[-2:]}"


def normalize_team_ref(raw: dict[str, Any]) -> TeamRef:
    return TeamRef(
        external_id=str(raw["id"]),
        name=raw.get("name") or raw.get("shortName") or "?",
        short_name=raw.get("tla") or raw.get("shortName"),
        logo_url=raw.get("crest"),
    )


def normalize_competition(raw: dict[str, Any]) -> CompetitionDTO:
    season = raw.get("currentSeason") or {}
    start = _parse_date(season.get("startDate"))
    return CompetitionDTO(
        external_id=raw["code"],
        name=raw["name"],
        country=(raw.get("area") or {}).get("name"),
        logo_url=raw.get("emblem"),
        season_key=str(start.year) if start else None,
        season_label=season_label(start.year) if start else None,
        season_start=start,
        season_end=_parse_date(season.get("endDate")),
    )


def normalize_player(raw: dict[str, Any]) -> PlayerDTO:
    return PlayerDTO(
        external_id=str(raw["id"]),
        name=raw["name"],
        position=raw.get("position"),
        nationality=raw.get("nationality"),
        extra={"date_of_birth": raw["dateOfBirth"]} if raw.get("dateOfBirth") else {},
    )


def normalize_team(raw: dict[str, Any]) -> TeamDTO:
    ref = normalize_team_ref(raw)
    return TeamDTO(
        **ref.model_dump(),
        country=(raw.get("area") or {}).get("name"),
        squad=[normalize_player(p) for p in raw.get("squad", [])],
    )


def normalize_match(raw: dict[str, Any]) -> EventDTO:
    score = raw.get("score") or {}
    full = score.get("fullTime") or {}
    status = STATUS_MAP.get(raw["status"], "scheduled")
    sides = (("home", raw["homeTeam"]), ("away", raw["awayTeam"]))
    return EventDTO(
        external_id=str(raw["id"]),
        kind="match",
        start_time=_parse_dt(raw["utcDate"]),
        status=status,
        venue=raw.get("venue"),
        round=str(raw["matchday"]) if raw.get("matchday") is not None else None,
        participants=[
            ParticipantDTO(team=normalize_team_ref(team), side=side, score=full.get(side))  # type: ignore[arg-type]
            for side, team in sides
        ],
        extra={
            "stage": raw.get("stage"),
            "winner": score.get("winner"),
            "half_time": score.get("halfTime"),
        },
    )


def normalize_standing_row(raw: dict[str, Any]) -> StandingDTO:
    return StandingDTO(
        team=normalize_team_ref(raw["team"]),
        position=raw["position"],
        played=raw.get("playedGames", 0),
        won=raw.get("won", 0),
        drawn=raw.get("draw", 0),
        lost=raw.get("lost", 0),
        points=raw.get("points", 0),
        extra={
            "goals_for": raw.get("goalsFor", 0),
            "goals_against": raw.get("goalsAgainst", 0),
            "goal_difference": raw.get("goalDifference", 0),
            "form": raw.get("form"),
        },
    )


def normalize_standings(raw: dict[str, Any]) -> list[StandingDTO]:
    """Use the overall (TOTAL) table; HOME/AWAY splits are ignored."""
    for table in raw.get("standings", []):
        if table.get("type") == TOTAL_STANDING_TYPE:
            return [normalize_standing_row(row) for row in table["table"]]
    return []


class FootballDataAdapter(HttpFixtureAdapter):
    sport_slug = "football"
    sport_name = "Futbol"
    source = "football-data"
    default_competitions = ("PL", "PD", "SA", "BL1", "CL")
    fixtures_subdir = "football_data"
    base_url = BASE_URL

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        super().__init__(
            settings,
            api_key=settings.football_data_api_key,
            headers={"X-Auth-Token": settings.football_data_api_key},
            min_interval=MIN_REQUEST_INTERVAL_SECONDS,
            client=client,
        )

    def shift_fixture_dates(self, data: dict[str, Any], delta: timedelta) -> None:
        for match in data.get("matches", []):
            match["utcDate"] = (_parse_dt(match["utcDate"]) + delta).isoformat()

    async def fetch_competitions(self) -> list[CompetitionDTO]:
        data = await self._request("/competitions", "competitions")
        return [normalize_competition(c) for c in data["competitions"]]

    async def fetch_events(self, competition_ext_id: str, season: str) -> list[EventDTO]:
        data = await self._request(
            f"/competitions/{competition_ext_id}/matches",
            f"{competition_ext_id}_matches",
            {"season": season},
        )
        return [normalize_match(m) for m in data["matches"]]

    async def fetch_standings(self, competition_ext_id: str, season: str) -> list[StandingDTO]:
        data = await self._request(
            f"/competitions/{competition_ext_id}/standings",
            f"{competition_ext_id}_standings",
            {"season": season},
        )
        return normalize_standings(data)

    async def fetch_teams(self, competition_ext_id: str, season: str) -> list[TeamDTO]:
        data = await self._request(
            f"/competitions/{competition_ext_id}/teams",
            f"{competition_ext_id}_teams",
            {"season": season},
        )
        return [normalize_team(t) for t in data["teams"]]
