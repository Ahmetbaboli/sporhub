"""balldontlie NBA adapter (https://docs.balldontlie.io, NBA API v1).

Verified against the docs:
  * base URL https://api.balldontlie.io/v1, key sent as the raw `Authorization` header
  * free tier: 5 requests/minute and only /teams, /players, /games
  * `/players/active` needs the ALL-STAR tier, `/standings` needs GOAT -> standings are
    computed here from regular-season results so the free tier is enough for them
  * cursor pagination: `per_page` <= 100, `meta.next_cursor` until it is absent
"""

import logging
from collections import defaultdict
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

logger = logging.getLogger(__name__)

BASE_URL = "https://api.balldontlie.io/v1"
# Free tier: 5 requests per minute -> one request every 12 s, plus a safety margin.
MIN_REQUEST_INTERVAL_SECONDS = 12.5
PER_PAGE = 100
MAX_PAGES = 40  # hard stop against a runaway cursor loop
COMPETITION_ID = "nba"
# An NBA season starts in October and is named after that calendar year (2026 = 2026/27).
SEASON_START_MONTH = 8
NBA_CONFERENCES = frozenset({"East", "West"})
UNAUTHORIZED = frozenset({401, 403})
FORM_LENGTH = 5

STATUS_STATE_MAP: dict[str, EventStatus] = {
    "scheduled": "scheduled",
    "in_progress": "live",
    "delayed": "live",
    "final": "finished",
    "postponed": "postponed",
    "suspended": "postponed",
    "abandoned": "postponed",
    "canceled": "cancelled",
    "unknown": "scheduled",
}


def current_season_year(today: date) -> int:
    return today.year if today.month >= SEASON_START_MONTH else today.year - 1


def season_label(start_year: int) -> str:
    return f"{start_year}/{str(start_year + 1)[-2:]}"


def normalize_team_ref(raw: dict[str, Any]) -> TeamRef:
    return TeamRef(
        external_id=str(raw["id"]),
        name=raw.get("full_name") or raw["name"],
        short_name=raw.get("abbreviation"),
    )


def normalize_team(raw: dict[str, Any]) -> TeamDTO:
    return TeamDTO(**normalize_team_ref(raw).model_dump(), country="USA")


def normalize_player(raw: dict[str, Any]) -> PlayerDTO:
    extra = {
        key: raw[key]
        for key in ("height", "weight", "jersey_number", "college", "draft_year")
        if raw.get(key)
    }
    return PlayerDTO(
        external_id=str(raw["id"]),
        name=f"{raw['first_name']} {raw['last_name']}".strip(),
        position=raw.get("position") or None,
        nationality=raw.get("country"),
        extra=extra,
    )


def normalize_status(raw: dict[str, Any]) -> EventStatus:
    state = raw.get("status_state")
    if state in STATUS_STATE_MAP:
        return STATUS_STATE_MAP[state]
    return "finished" if raw.get("status") == "Final" else "scheduled"


def _start_time(raw: dict[str, Any]) -> datetime:
    value = raw.get("datetime")
    if value:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    return datetime.fromisoformat(raw["date"]).replace(tzinfo=UTC)


def normalize_game(raw: dict[str, Any]) -> EventDTO:
    status = normalize_status(raw)
    has_score = status in ("live", "finished")
    sides = (
        ("home", raw["home_team"], raw.get("home_team_score")),
        ("away", raw["visitor_team"], raw.get("visitor_team_score")),
    )
    return EventDTO(
        external_id=str(raw["id"]),
        kind="match",
        start_time=_start_time(raw),
        status=status,
        round="Playoffs" if raw.get("postseason") else None,
        participants=[
            ParticipantDTO(
                team=normalize_team_ref(team),
                side=side,  # type: ignore[arg-type]
                score=score if has_score else None,
            )
            for side, team, score in sides
        ],
        extra={
            "postseason": bool(raw.get("postseason")),
            "period": raw.get("period"),
            "clock": raw.get("time"),
            "status_text": raw.get("status"),
        },
    )


def compute_standings(
    games: list[EventDTO], teams: list[TeamDTO], conferences: dict[str, tuple[str, str]]
) -> list[StandingDTO]:
    """League table from finished regular-season games. `conferences`: team id -> (conf, div)."""
    record: dict[str, dict[str, Any]] = {
        t.external_id: {"won": 0, "lost": 0, "pf": 0, "pa": 0, "form": []} for t in teams
    }
    ordered = sorted(
        (g for g in games if g.status == "finished" and not g.extra.get("postseason")),
        key=lambda g: g.start_time,
    )
    for game in ordered:
        home, away = game.participants
        if home.team is None or away.team is None or home.score is None or away.score is None:
            continue
        for me, other in ((home, away), (away, home)):
            row = record.get(me.team.external_id)  # type: ignore[union-attr]
            if row is None:
                continue
            won = me.score > other.score  # type: ignore[operator]
            row["won" if won else "lost"] += 1
            row["pf"] += me.score
            row["pa"] += other.score
            row["form"].append("W" if won else "L")

    def win_pct(row: dict[str, Any]) -> float:
        played = row["won"] + row["lost"]
        return row["won"] / played if played else 0.0

    refs = {t.external_id: t for t in teams}
    ranking = sorted(
        record, key=lambda tid: (-win_pct(record[tid]), -record[tid]["won"], refs[tid].name)
    )
    conference_rank: dict[str, int] = defaultdict(int)
    rows: list[StandingDTO] = []
    for position, tid in enumerate(ranking, start=1):
        row = record[tid]
        conference, division = conferences.get(tid, ("", ""))
        conference_rank[conference] += 1
        rows.append(
            StandingDTO(
                team=TeamRef(**refs[tid].model_dump(include=set(TeamRef.model_fields))),
                position=position,
                played=row["won"] + row["lost"],
                won=row["won"],
                lost=row["lost"],
                points=row["won"],
                extra={
                    "conference": conference,
                    "division": division,
                    "conference_rank": conference_rank[conference],
                    "win_pct": round(win_pct(row), 3),
                    "points_for": row["pf"],
                    "points_against": row["pa"],
                    "form": ",".join(row["form"][-FORM_LENGTH:]) or None,
                },
            )
        )
    return rows


class BallDontLieAdapter(HttpFixtureAdapter):
    sport_slug = "basketball"
    sport_name = "Basketbol"
    source = "balldontlie"
    default_competitions = (COMPETITION_ID,)
    fixtures_subdir = "balldontlie"
    base_url = BASE_URL

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        super().__init__(
            settings,
            api_key=settings.balldontlie_api_key,
            headers={"Authorization": settings.balldontlie_api_key},
            min_interval=MIN_REQUEST_INTERVAL_SECONDS,
            client=client,
        )
        self._raw_teams: list[dict[str, Any]] | None = None
        self._games: dict[str, list[EventDTO]] = {}

    def shift_fixture_dates(self, data: dict[str, Any], delta: timedelta) -> None:
        for game in data.get("data", []):
            if game.get("datetime"):
                shifted = datetime.fromisoformat(game["datetime"].replace("Z", "+00:00")) + delta
                game["datetime"] = shifted.isoformat()
            if game.get("date"):
                game["date"] = (date.fromisoformat(game["date"][:10]) + delta).isoformat()

    async def _pages(
        self, path: str, fixture: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        cursor: int | None = None
        for _ in range(MAX_PAGES):
            query = {"per_page": PER_PAGE, **(params or {})}
            if cursor is not None:
                query["cursor"] = cursor
            page = await self._request(path, fixture, query)
            items.extend(page["data"])
            cursor = (page.get("meta") or {}).get("next_cursor")
            if cursor is None:
                return items
        logger.warning("pagination stopped at MAX_PAGES", extra={"path": path})
        return items

    async def _team_rows(self) -> list[dict[str, Any]]:
        if self._raw_teams is None:
            rows = await self._pages("/teams", "teams")
            # The endpoint can include historical/non-NBA franchises; real ones have a conference.
            self._raw_teams = [r for r in rows if r.get("conference") in NBA_CONFERENCES]
        return self._raw_teams

    async def fetch_competitions(self) -> list[CompetitionDTO]:
        today = self._fixture_today or datetime.now(UTC).date()
        year = current_season_year(today)
        return [
            CompetitionDTO(
                external_id=COMPETITION_ID,
                name="NBA",
                country="USA",
                season_key=str(year),
                season_label=season_label(year),
            )
        ]

    async def fetch_teams(self, competition_ext_id: str, season: str) -> list[TeamDTO]:
        teams = {str(r["id"]): normalize_team(r) for r in await self._team_rows()}
        try:
            players = await self._pages("/players/active", "players_active")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code not in UNAUTHORIZED:
                raise
            logger.warning("rosters need the ALL-STAR tier; syncing teams without players")
            return list(teams.values())
        for raw in players:
            team = teams.get(str((raw.get("team") or {}).get("id")))
            if team is not None:
                team.squad.append(normalize_player(raw))
        return list(teams.values())

    async def fetch_events(self, competition_ext_id: str, season: str) -> list[EventDTO]:
        if season not in self._games:
            games: dict[str, EventDTO] = {}
            for season_type in ("regular", "playoffs"):
                rows = await self._pages(
                    "/games",
                    f"games_{season_type}",
                    {"seasons[]": season, "season_type": season_type},
                )
                for raw in rows:
                    games[str(raw["id"])] = normalize_game(raw)
            self._games[season] = sorted(games.values(), key=lambda g: g.start_time)
        return self._games[season]

    async def fetch_standings(self, competition_ext_id: str, season: str) -> list[StandingDTO]:
        rows = await self._team_rows()
        teams = [normalize_team(r) for r in rows]
        conferences = {str(r["id"]): (r["conference"], r.get("division", "")) for r in rows}
        return compute_standings(
            await self.fetch_events(competition_ext_id, season), teams, conferences
        )
