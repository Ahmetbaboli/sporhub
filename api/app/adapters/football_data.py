"""football-data.org v4 adapter.

Docs: https://docs.football-data.org/general/v4/ — auth via `X-Auth-Token`,
free tier allows 10 requests/minute.
"""

import json
import logging
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from app.adapters.base import BaseAdapter
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
from app.adapters.http import RateLimitedClient
from app.core.config import Settings

logger = logging.getLogger(__name__)

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


class FootballDataAdapter(BaseAdapter):
    sport_slug = "football"
    sport_name = "Futbol"
    source = "football-data"
    default_competitions = ("PL", "PD", "SA", "BL1", "CL")

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._fixtures_dir: Path = settings.fixtures_dir / "football_data"
        self._today = date.fromisoformat(settings.fixture_today) if settings.fixture_today else None
        self.use_fixtures = settings.use_fixtures or not settings.football_data_api_key
        if self.use_fixtures and not settings.use_fixtures:
            logger.warning("FOOTBALL_DATA_API_KEY missing; falling back to fixtures")
        self._http: RateLimitedClient | None = None
        if not self.use_fixtures:
            self._http = RateLimitedClient(
                BASE_URL,
                headers={"X-Auth-Token": settings.football_data_api_key},
                min_interval=MIN_REQUEST_INTERVAL_SECONDS,
                client=client,
            )

    async def _get(self, path: str, fixture: str, params: dict[str, Any] | None = None) -> Any:
        if self._http is None:
            return self._load_fixture(fixture)
        return await self._http.get_json(path, params)

    def _load_fixture(self, name: str) -> dict[str, Any]:
        data = json.loads((self._fixtures_dir / f"{name}.json").read_text(encoding="utf-8"))
        return self._shift_dates(data)

    def _shift_dates(self, data: dict[str, Any]) -> dict[str, Any]:
        """Move fixture match dates so the sample 'today' lines up with the real today."""
        reference = (data.get("_fixture") or {}).get("reference_date")
        if not reference or "matches" not in data:
            return data
        today = self._today or datetime.now(UTC).date()
        shift = timedelta(days=(today - date.fromisoformat(reference)).days)
        for match in data["matches"]:
            match["utcDate"] = (_parse_dt(match["utcDate"]) + shift).isoformat()
        return data

    async def fetch_competitions(self) -> list[CompetitionDTO]:
        data = await self._get("/competitions", "competitions")
        return [normalize_competition(c) for c in data["competitions"]]

    async def fetch_events(self, competition_ext_id: str, season: str) -> list[EventDTO]:
        data = await self._get(
            f"/competitions/{competition_ext_id}/matches",
            f"{competition_ext_id}_matches",
            {"season": season},
        )
        return [normalize_match(m) for m in data["matches"]]

    async def fetch_standings(self, competition_ext_id: str, season: str) -> list[StandingDTO]:
        data = await self._get(
            f"/competitions/{competition_ext_id}/standings",
            f"{competition_ext_id}_standings",
            {"season": season},
        )
        return normalize_standings(data)

    async def fetch_teams(self, competition_ext_id: str, season: str) -> list[TeamDTO]:
        data = await self._get(
            f"/competitions/{competition_ext_id}/teams",
            f"{competition_ext_id}_teams",
            {"season": season},
        )
        return [normalize_team(t) for t in data["teams"]]

    async def aclose(self) -> None:
        if self._http:
            await self._http.aclose()
