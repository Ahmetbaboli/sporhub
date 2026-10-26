"""Jolpica-F1 adapter (Ergast-compatible API) — Formula 1.

Verified against https://github.com/jolpica/jolpica-f1 docs:
  * base URL https://api.jolpi.ca/ergast/f1, no API key
  * unauthenticated limits: 4 requests/second burst, 500 requests/hour sustained
  * `limit` (default 30, max 100) and `offset` paginate flattened rows; endpoints end in `/`
  * a descriptive User-Agent is required
  * every number arrives as a string
"""

import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx

from app.adapters.dto import (
    CompetitionDTO,
    EventDTO,
    ParticipantDTO,
    PlayerDTO,
    StandingDTO,
    TeamDTO,
    TeamRef,
)
from app.adapters.http_fixture import HttpFixtureAdapter
from app.core.config import Settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.jolpi.ca/ergast/f1"
USER_AGENT = "JustSport/0.2 (open-source sports data portfolio project)"
# 4 req/s burst -> 0.3 s spacing; a full season sync is ~10 requests, far below 500/hour.
MIN_REQUEST_INTERVAL_SECONDS = 0.3
PAGE_LIMIT = 100
MAX_PAGES = 20
COMPETITION_ID = "f1"
DEFAULT_RACE_TIME = "12:00:00Z"
SESSION_KEYS = {
    "FirstPractice": "fp1",
    "SecondPractice": "fp2",
    "ThirdPractice": "fp3",
    "Qualifying": "qualifying",
    "Sprint": "sprint",
    "SprintQualifying": "sprint_qualifying",
}


def _utc(day: str, time: str | None) -> datetime:
    stamp = f"{day}T{(time or DEFAULT_RACE_TIME).replace('Z', '')}+00:00"
    return datetime.fromisoformat(stamp).astimezone(UTC)


def _int(value: str | None) -> int | None:
    return int(value) if value not in (None, "") else None


def _constructor_ref(raw: dict[str, Any]) -> TeamRef:
    return TeamRef(external_id=raw["constructorId"], name=raw["name"])


def normalize_constructor(raw: dict[str, Any]) -> TeamDTO:
    return TeamDTO(**_constructor_ref(raw).model_dump(), country=raw.get("nationality"))


def normalize_driver(raw: dict[str, Any]) -> PlayerDTO:
    extra = {
        "code": raw.get("code"),
        "number": raw.get("permanentNumber"),
        "date_of_birth": raw.get("dateOfBirth"),
    }
    return PlayerDTO(
        external_id=raw["driverId"],
        name=f"{raw['givenName']} {raw['familyName']}",
        position="Driver",
        nationality=raw.get("nationality"),
        extra={k: v for k, v in extra.items() if v},
    )


def normalize_result(raw: dict[str, Any]) -> ParticipantDTO:
    driver = raw["Driver"]
    fastest = raw.get("FastestLap") or {}
    return ParticipantDTO(
        team=_constructor_ref(raw["Constructor"]),
        player_external_id=driver["driverId"],
        position=_int(raw.get("position")),
        points=float(raw.get("points", 0)),
        extra={
            "driver": f"{driver['givenName']} {driver['familyName']}",
            "code": driver.get("code"),
            "grid": _int(raw.get("grid")),
            "laps": _int(raw.get("laps")),
            "status": raw.get("status"),
            "time": (raw.get("Time") or {}).get("time"),
            "position_text": raw.get("positionText"),
            "fastest_lap_rank": _int(fastest.get("rank")),
        },
    )


def normalize_race(raw: dict[str, Any]) -> EventDTO:
    circuit = raw["Circuit"]
    place = circuit["Location"]
    results = [normalize_result(r) for r in raw.get("Results", [])]
    sessions = {
        name: _utc(raw[key]["date"], raw[key].get("time")).isoformat()
        for key, name in SESSION_KEYS.items()
        if raw.get(key)
    }
    return EventDTO(
        external_id=f"{raw['season']}-{raw['round']}",
        kind="race",
        name=raw["raceName"],
        start_time=_utc(raw["date"], raw.get("time")),
        status="finished" if results else "scheduled",
        venue=f"{circuit['circuitName']}, {place['locality']}, {place['country']}",
        round=str(raw["round"]),
        participants=sorted(results, key=lambda p: p.position or 99),
        extra={
            "circuit_id": circuit["circuitId"],
            "locality": place["locality"],
            "country": place["country"],
            "sessions": sessions,
        },
    )


def normalize_driver_standings(standings_list: dict[str, Any]) -> list[StandingDTO]:
    completed_rounds = int(standings_list.get("round") or 0)
    rows = []
    for raw in standings_list.get("DriverStandings", []):
        constructors = raw.get("Constructors") or []
        driver = raw["Driver"]
        rows.append(
            StandingDTO(
                team=_constructor_ref(constructors[-1]) if constructors else None,
                player_external_id=driver["driverId"],
                position=int(raw["position"]),
                played=completed_rounds,
                won=int(raw.get("wins", 0)),
                points=float(raw["points"]),
                extra={"kind": "driver", "code": driver.get("code")},
            )
        )
    return rows


def normalize_constructor_standings(standings_list: dict[str, Any]) -> list[StandingDTO]:
    completed_rounds = int(standings_list.get("round") or 0)
    return [
        StandingDTO(
            team=_constructor_ref(raw["Constructor"]),
            position=int(raw["position"]),
            played=completed_rounds,
            won=int(raw.get("wins", 0)),
            points=float(raw["points"]),
            extra={"kind": "constructor"},
        )
        for raw in standings_list.get("ConstructorStandings", [])
    ]


def _first_list(data: dict[str, Any]) -> dict[str, Any]:
    lists = data["MRData"]["StandingsTable"]["StandingsLists"]
    return lists[0] if lists else {}


class JolpicaAdapter(HttpFixtureAdapter):
    sport_slug = "formula-1"
    sport_name = "Formula 1"
    source = "jolpica"
    default_competitions = (COMPETITION_ID,)
    fixtures_subdir = "jolpica"
    base_url = BASE_URL
    requires_api_key = False

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        super().__init__(
            settings,
            headers={"User-Agent": USER_AGENT},
            min_interval=MIN_REQUEST_INTERVAL_SECONDS,
            client=client,
        )
        self._races: dict[str, list[dict[str, Any]]] = {}

    def shift_fixture_dates(self, data: dict[str, Any], delta: timedelta) -> None:
        for race in data.get("MRData", {}).get("RaceTable", {}).get("Races", []):
            for holder in (race, *(race[k] for k in SESSION_KEYS if race.get(k))):
                holder["date"] = (date.fromisoformat(holder["date"]) + delta).isoformat()

    async def _paged(self, path: str, fixture: str, table: str, rows_key: str) -> list[dict]:
        """Collect `rows_key` rows of MRData[table], following limit/offset pagination."""
        collected: list[dict[str, Any]] = []
        offset = 0
        for _ in range(MAX_PAGES):
            data = await self._request(path, fixture, {"limit": PAGE_LIMIT, "offset": offset})
            mr = data["MRData"]
            collected.extend(mr[table][rows_key])
            offset += int(mr.get("limit") or PAGE_LIMIT)
            if offset >= int(mr.get("total") or 0):
                break
        return collected

    async def _schedule(self, season: str) -> list[dict[str, Any]]:
        if season not in self._races:
            self._races[season] = await self._paged(
                f"/{season}/races/", f"{season}_races", "RaceTable", "Races"
            )
        return self._races[season]

    def _fixture_season(self) -> str:
        return str((self._fixture_today or datetime.now(UTC).date()).year)

    async def _season_year(self) -> str:
        if self.use_fixtures:  # fixtures hold one fixed season, whatever "today" is
            return str(
                sorted(p.stem.split("_")[0] for p in self._fixtures_dir.glob("*_races.json"))[-1]
            )
        return self._fixture_season()

    async def fetch_competitions(self) -> list[CompetitionDTO]:
        season = await self._season_year()
        races = await self._schedule(season)
        dates = [r["date"] for r in races]
        return [
            CompetitionDTO(
                external_id=COMPETITION_ID,
                name="Formula 1",
                country="World",
                season_key=season,
                season_label=season,
                season_start=date.fromisoformat(min(dates)) if dates else None,
                season_end=date.fromisoformat(max(dates)) if dates else None,
            )
        ]

    async def fetch_teams(self, competition_ext_id: str, season: str) -> list[TeamDTO]:
        data = await self._request(
            f"/{season}/constructors/",
            f"{season}_constructors",
            {"limit": PAGE_LIMIT},
        )
        teams = {
            c["constructorId"]: normalize_constructor(c)
            for c in data["MRData"]["ConstructorTable"]["Constructors"]
        }
        standings = _first_list(
            await self._request(
                f"/{season}/driverstandings/", f"{season}_driverstandings", {"limit": PAGE_LIMIT}
            )
        )
        for raw in standings.get("DriverStandings", []):
            constructors = raw.get("Constructors") or []
            team = teams.get(constructors[-1]["constructorId"]) if constructors else None
            if team is not None:
                team.squad.append(normalize_driver(raw["Driver"]))
        return list(teams.values())

    async def fetch_events(self, competition_ext_id: str, season: str) -> list[EventDTO]:
        races = {r["round"]: {**r, "Results": []} for r in await self._schedule(season)}
        results = await self._paged(
            f"/{season}/results/", f"{season}_results", "RaceTable", "Races"
        )
        # A page boundary can split one race's results across two pages: merge by round.
        for part in results:
            races.setdefault(part["round"], {**part, "Results": []})["Results"].extend(
                part.get("Results", [])
            )
        return [normalize_race(r) for r in sorted(races.values(), key=lambda r: int(r["round"]))]

    async def fetch_standings(self, competition_ext_id: str, season: str) -> list[StandingDTO]:
        drivers = _first_list(
            await self._request(
                f"/{season}/driverstandings/", f"{season}_driverstandings", {"limit": PAGE_LIMIT}
            )
        )
        constructors = _first_list(
            await self._request(
                f"/{season}/constructorstandings/",
                f"{season}_constructorstandings",
                {"limit": PAGE_LIMIT},
            )
        )
        return normalize_driver_standings(drivers) + normalize_constructor_standings(constructors)
