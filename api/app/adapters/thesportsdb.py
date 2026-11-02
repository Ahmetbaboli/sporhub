"""TheSportsDB v1 adapter: Turkish Süper Lig and TFF 1. Lig.

Docs: https://www.thesportsdb.com/documentation (read 2026-11-02, see docs/DATA-SOURCES.md):
  * key in the path: /api/v1/json/{key}/...; premium 100 requests/minute, 429 when exceeded
  * the public development key "123" returns truncated results (5 table rows, 15 events) and
    the terms allow it only for development — live mode therefore treats it as "not configured"
  * strTimestamp is UTC; scores are strings or null; strPostponed "yes" marks postponements
"""

from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx

from app.adapters.dto import (
    CompetitionDTO,
    EventDTO,
    EventStatus,
    ParticipantDTO,
    StandingDTO,
    TeamDTO,
    TeamRef,
)
from app.adapters.http_fixture import HttpFixtureAdapter
from app.core.config import Settings
from app.core.data_mode import is_demo

BASE_URL = "https://www.thesportsdb.com/api/v1/json"
DEVELOPMENT_KEY = "123"
# Premium: 100 requests/minute -> one request every 0.6 s, plus margin.
MIN_REQUEST_INTERVAL_SECONDS = 0.7

LEAGUES: dict[str, str] = {"4339": "Süper Lig", "4676": "TFF 1. Lig"}
COUNTRY = "Turkey"

STATUS_MAP: dict[str, EventStatus] = {
    "NS": "scheduled",
    "TBD": "scheduled",
    "NOT STARTED": "scheduled",
    "1H": "live",
    "HT": "live",
    "2H": "live",
    "ET": "live",
    "BT": "live",
    "P": "live",
    "LIVE": "live",
    "INT": "live",
    "FT": "finished",
    "AET": "finished",
    "PEN": "finished",
    "AWD": "finished",
    "WO": "finished",
    "MATCH FINISHED": "finished",
    "PST": "postponed",
    "POSTPONED": "postponed",
    "SUSP": "postponed",
    "CANC": "cancelled",
    "CANCELLED": "cancelled",
    "ABD": "cancelled",
}


def _int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def season_label(season: str) -> str:
    """'2026-2027' -> '2026/27'."""
    start, _, end = season.partition("-")
    return f"{start}/{end[-2:]}" if end else season


def parse_timestamp(event: dict[str, Any]) -> datetime:
    """strTimestamp is UTC without an offset; fall back to dateEvent + strTime."""
    raw = event.get("strTimestamp")
    if raw:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    else:
        time = (event.get("strTime") or "00:00:00").split("+")[0]
        parsed = datetime.fromisoformat(f"{event['dateEvent']}T{time}")
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)).astimezone(UTC)


def map_status(event: dict[str, Any]) -> EventStatus:
    if str(event.get("strPostponed") or "").lower() == "yes":
        return "postponed"
    status = STATUS_MAP.get(str(event.get("strStatus") or "").strip().upper())
    if status:
        return status
    # Unknown/empty status: a past kick-off with both scores is finished, otherwise scheduled.
    has_score = _int(event.get("intHomeScore")) is not None
    return "finished" if has_score and parse_timestamp(event) < datetime.now(UTC) else "scheduled"


def _team_ref(event: dict[str, Any], side: str) -> TeamRef:
    return TeamRef(external_id=str(event[f"id{side}Team"]), name=event[f"str{side}Team"])


def normalize_event(event: dict[str, Any]) -> EventDTO:
    status = map_status(event)
    keep_score = status in ("live", "finished")
    return EventDTO(
        external_id=str(event["idEvent"]),
        kind="match",
        start_time=parse_timestamp(event),
        status=status,
        venue=event.get("strVenue") or None,
        round=str(event["intRound"]) if event.get("intRound") not in (None, "") else None,
        participants=[
            ParticipantDTO(
                team=_team_ref(event, side),
                side=side.lower(),  # type: ignore[arg-type]
                score=_int(event.get(f"int{side}Score")) if keep_score else None,
            )
            for side in ("Home", "Away")
        ],
        extra={"status_code": event.get("strStatus")},
    )


def normalize_form(form: str | None) -> str | None:
    """'WWDLW' -> 'W,W,D,L,W' (the shared format used by the standings table)."""
    letters = [c for c in (form or "").upper() if c in "WDL"]
    return ",".join(letters) or None


def normalize_standing(row: dict[str, Any]) -> StandingDTO:
    return StandingDTO(
        team=TeamRef(external_id=str(row["idTeam"]), name=row["strTeam"]),
        position=_int(row.get("intRank")) or 0,
        played=_int(row.get("intPlayed")) or 0,
        won=_int(row.get("intWin")) or 0,
        drawn=_int(row.get("intDraw")) or 0,
        lost=_int(row.get("intLoss")) or 0,
        points=float(_int(row.get("intPoints")) or 0),
        extra={
            "goals_for": _int(row.get("intGoalsFor")),
            "goals_against": _int(row.get("intGoalsAgainst")),
            "goal_difference": _int(row.get("intGoalDifference")),
            "form": normalize_form(row.get("strForm")),
            "description": row.get("strDescription"),
        },
    )


def normalize_team(raw: dict[str, Any]) -> TeamDTO:
    return TeamDTO(
        external_id=str(raw["idTeam"]),
        name=raw["strTeam"],
        short_name=raw.get("strTeamShort") or None,
        country=raw.get("strCountry") or None,
    )


class TheSportsDbAdapter(HttpFixtureAdapter):
    sport_slug = "football"
    sport_name = "Futbol"
    source = "thesportsdb"
    default_competitions = tuple(LEAGUES)
    fixtures_subdir = "thesportsdb"
    base_url = BASE_URL
    # Free plan has no livescores; premium livescores are ~2 minutes behind.
    scores_delayed = True

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        key = settings.thesportsdb_api_key
        # The development key returns truncated tables: never present those as a real league.
        usable = "" if (key == DEVELOPMENT_KEY and not is_demo(settings)) else key
        self._key = usable
        super().__init__(
            settings,
            api_key=usable,
            min_interval=MIN_REQUEST_INTERVAL_SECONDS,
            client=client,
        )

    def _path(self, endpoint: str) -> str:
        return f"/{self._key}/{endpoint}"

    def shift_fixture_dates(self, data: dict[str, Any], delta: timedelta) -> None:
        for event in data.get("events") or []:
            moved = parse_timestamp(event) + delta
            event["strTimestamp"] = moved.strftime("%Y-%m-%dT%H:%M:%S")
            event["dateEvent"] = moved.date().isoformat()

    async def _league(self, league_id: str) -> dict[str, Any]:
        data = await self._request(
            self._path("lookupleague.php"), f"league_{league_id}", {"id": league_id}
        )
        return (data.get("leagues") or [{}])[0]

    async def fetch_competitions(self) -> list[CompetitionDTO]:
        comps = []
        for league_id, name in LEAGUES.items():
            league = await self._league(league_id)
            season = league.get("strCurrentSeason")
            start = date.fromisoformat(f"{season[:4]}-07-01") if season else None
            comps.append(
                CompetitionDTO(
                    external_id=league_id,
                    name=name,
                    country=COUNTRY,
                    season_key=season,
                    season_label=season_label(season) if season else None,
                    season_start=start,
                )
            )
        return comps

    async def fetch_events(self, competition_ext_id: str, season: str) -> list[EventDTO]:
        data = await self._request(
            self._path("eventsseason.php"),
            f"season_{competition_ext_id}",
            {"id": competition_ext_id, "s": season},
        )
        return [normalize_event(e) for e in data.get("events") or []]

    async def fetch_standings(self, competition_ext_id: str, season: str) -> list[StandingDTO]:
        data = await self._request(
            self._path("lookuptable.php"),
            f"table_{competition_ext_id}",
            {"l": competition_ext_id, "s": season},
        )
        return [normalize_standing(r) for r in data.get("table") or []]

    async def fetch_teams(self, competition_ext_id: str, season: str) -> list[TeamDTO]:
        data = await self._request(
            self._path("lookup_all_teams.php"),
            f"teams_{competition_ext_id}",
            {"id": competition_ext_id},
        )
        return [normalize_team(t) for t in data.get("teams") or []]
