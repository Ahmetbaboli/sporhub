"""ESPN site API adapter: Turkish Süper Lig (free, keyless, unofficial).

Read 2026-11-03 (see docs/DATA-SOURCES.md):
  * https://site.api.espn.com/apis/site/v2/sports/soccer/tur.1/{scoreboard,teams} and
    https://site.api.espn.com/apis/v2/sports/soccer/tur.1/standings; no key, no documented
    limits or terms for third parties. It is ESPN's own web/app backend, not a public product.
  * so it is opt-in (ESPN_ENABLED=true, for personal/non-commercial use), with a small request
    budget (budget.py) and a full season in ~12 monthly scoreboard requests (dates=YYYYMM).
  * times are UTC ("2026-10-09T17:00Z"); status.type.state is pre/in/post.
  * ESPN carries no TFF 1. Lig data (tur.2 is empty), so only the Süper Lig is offered.
"""

from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx

from app.adapters.dto import (
    CompetitionDTO,
    EventDTO,
    EventStatus,
    IncidentDTO,
    IncidentKind,
    LineupDTO,
    LineupPlayerDTO,
    MatchDetailsDTO,
    MatchStatDTO,
    ParticipantDTO,
    Side,
    StandingDTO,
    TeamDTO,
    TeamRef,
    hex_color,
)
from app.adapters.http_fixture import HttpFixtureAdapter
from app.core.config import Settings

BASE_URL = "https://site.api.espn.com/apis"
LEAGUES: dict[str, str] = {"tur.1": "Süper Lig"}
COUNTRY = "Turkey"
USER_AGENT = "JustSport/0.5 (open-source sports data portfolio project)"
MIN_REQUEST_INTERVAL_SECONDS = 2.0
SEASON_MONTHS = 12
# ESPN seasons are labelled by their first year and run July -> June.
SEASON_START_MONTH = 7
ENABLED_MARKER = "enabled"

STATUS_BY_NAME: dict[str, EventStatus] = {
    "STATUS_POSTPONED": "postponed",
    "STATUS_DELAYED": "postponed",
    "STATUS_SUSPENDED": "postponed",
    "STATUS_CANCELED": "cancelled",
    "STATUS_ABANDONED": "cancelled",
    "STATUS_FORFEIT": "finished",
}
STATUS_BY_STATE: dict[str, EventStatus] = {"pre": "scheduled", "in": "live", "post": "finished"}


def _int(value: Any) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def parse_time(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(UTC)


def season_label(year: int) -> str:
    return f"{year}/{str(year + 1)[-2:]}"


def season_months(year: int) -> list[str]:
    """'2026' -> ['202607', '202608', ..., '202706']."""
    months = []
    for i in range(SEASON_MONTHS):
        month = SEASON_START_MONTH + i
        months.append(f"{year + (month - 1) // 12}{(month - 1) % 12 + 1:02d}")
    return months


def map_status(status: dict[str, Any]) -> EventStatus:
    kind = status.get("type") or {}
    return STATUS_BY_NAME.get(kind.get("name", "")) or STATUS_BY_STATE.get(
        kind.get("state", ""), "scheduled"
    )


def _logo(team: dict[str, Any]) -> str | None:
    if team.get("logo"):
        return team["logo"]
    logos = team.get("logos") or []
    return logos[0].get("href") if logos else None


# ESPN's default for clubs it has no kit for (checked 2026-11-04: Alanyaspor, Göztepe, Samsunspor…
# all come back black/black or black/red). Showing it would paint those clubs wrongly.
PLACEHOLDER_PRIMARY = "#000000"
PLACEHOLDER_ALTERNATES = frozenset({"#000000", "#c60000"})


def team_colors(team: dict[str, Any]) -> dict[str, str | None]:
    color, alternate = hex_color(team.get("color")), hex_color(team.get("alternateColor"))
    if color == PLACEHOLDER_PRIMARY and (alternate is None or alternate in PLACEHOLDER_ALTERNATES):
        return {"color": None, "alternate_color": None}
    return {"color": color, "alternate_color": alternate}


def team_ref(team: dict[str, Any]) -> TeamRef:
    return TeamRef(
        external_id=str(team["id"]),
        name=team.get("displayName") or team["name"],
        short_name=team.get("abbreviation"),
        logo_url=_logo(team),
        **team_colors(team),
    )


def normalize_event(raw: dict[str, Any]) -> EventDTO:
    comp = raw["competitions"][0]
    status = map_status(raw.get("status") or comp.get("status") or {})
    keep_score = status in ("live", "finished")
    participants = [
        ParticipantDTO(
            team=team_ref(c["team"]),
            side=c.get("homeAway"),
            score=_int(c.get("score")) if keep_score else None,
            extra={"form": c["form"]} if c.get("form") else {},
        )
        for c in comp.get("competitors", [])
    ]
    clock = (raw.get("status") or {}).get("displayClock")
    return EventDTO(
        external_id=str(raw["id"]),
        kind="match",
        start_time=parse_time(raw["date"]),
        status=status,
        venue=(comp.get("venue") or {}).get("fullName"),
        participants=sorted(participants, key=lambda p: p.side != "home"),
        extra={"clock": clock} if status == "live" and clock else {},
    )


def _stat(entry: dict[str, Any], name: str) -> float | None:
    for stat in entry.get("stats", []):
        if stat.get("name") == name:
            return stat.get("value")
    return None


def normalize_standing(entry: dict[str, Any]) -> StandingDTO:
    note = entry.get("note") or {}
    return StandingDTO(
        team=team_ref(entry["team"]),
        position=_int(_stat(entry, "rank")) or 0,
        played=_int(_stat(entry, "gamesPlayed")) or 0,
        won=_int(_stat(entry, "wins")) or 0,
        drawn=_int(_stat(entry, "ties")) or 0,
        lost=_int(_stat(entry, "losses")) or 0,
        points=float(_stat(entry, "points") or 0),
        extra={
            "goals_for": _int(_stat(entry, "pointsFor")),
            "goals_against": _int(_stat(entry, "pointsAgainst")),
            "goal_difference": _int(_stat(entry, "pointDifferential")),
            # The provider's own qualification/relegation zone for this place.
            "zone": note.get("description"),
            "zone_color": note.get("color"),
        },
    )


# ESPN boxscore stat name -> our key, in display order. Pass accuracy is derived from counts.
MATCH_STAT_KEYS: dict[str, str] = {
    "possessionPct": "possession",
    "totalShots": "shots",
    "shotsOnTarget": "shots_on_target",
    "wonCorners": "corners",
    "foulsCommitted": "fouls",
    "yellowCards": "yellow_cards",
    "redCards": "red_cards",
    "offsides": "offsides",
    "saves": "saves",
    "totalPasses": "passes",
}
PASS_ACCURACY_KEY = "pass_accuracy"
PERCENT = 100


def _team_stats(team: dict[str, Any]) -> dict[str, float]:
    raw = {s.get("name"): _float(s.get("displayValue")) for s in team.get("statistics") or []}
    stats = {key: raw[name] for name, key in MATCH_STAT_KEYS.items() if raw.get(name) is not None}
    accurate, total = raw.get("accuratePasses"), raw.get("totalPasses")
    if accurate is not None and total:
        stats[PASS_ACCURACY_KEY] = round(accurate / total * PERCENT)
    return stats


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_match_stats(boxscore: dict[str, Any]) -> list[MatchStatDTO]:
    by_side = {t.get("homeAway"): _team_stats(t) for t in boxscore.get("teams") or []}
    home, away = by_side.get("home", {}), by_side.get("away", {})
    order = [*MATCH_STAT_KEYS.values(), PASS_ACCURACY_KEY]
    return [
        MatchStatDTO(key=key, home=home.get(key), away=away.get(key))
        for key in order
        if key in home or key in away
    ]


def _lineup_player(entry: dict[str, Any]) -> LineupPlayerDTO:
    athlete = entry.get("athlete") or {}
    return LineupPlayerDTO(
        external_id=str(athlete["id"]) if athlete.get("id") else None,
        name=athlete.get("displayName") or athlete.get("fullName") or "?",
        number=entry.get("jersey"),
        position=(entry.get("position") or {}).get("abbreviation"),
        subbed_in=bool(entry.get("subbedIn")),
        subbed_out=bool(entry.get("subbedOut")),
    )


def normalize_lineup(roster: dict[str, Any]) -> LineupDTO | None:
    entries = roster.get("roster") or []
    if roster.get("homeAway") not in ("home", "away") or not entries:
        return None
    starters = sorted(
        (e for e in entries if e.get("starter")), key=lambda e: _int(e.get("formationPlace")) or 0
    )
    return LineupDTO(
        side=roster["homeAway"],
        formation=roster.get("formation"),
        starters=[_lineup_player(e) for e in starters],
        substitutes=[_lineup_player(e) for e in entries if not e.get("starter")],
    )


def incident_kind(raw: dict[str, Any]) -> IncidentKind | None:
    kind = ((raw.get("type") or {}).get("type") or "").lower()
    if raw.get("scoringPlay"):
        if "own" in kind:
            return "own_goal"
        return "penalty_goal" if "penalty" in kind else "goal"
    if "substitution" in kind:
        return "substitution"
    if "red" in kind:  # also "yellow-red" (second yellow)
        return "red_card"
    return "yellow_card" if "yellow" in kind else None


def normalize_incident(raw: dict[str, Any], sides: dict[str, Side]) -> IncidentDTO | None:
    kind = incident_kind(raw)
    if kind is None:
        return None
    names = [(p.get("athlete") or {}).get("displayName") for p in raw.get("participants") or []]
    return IncidentDTO(
        minute=(raw.get("clock") or {}).get("displayValue") or "",
        kind=kind,
        side=sides.get(str((raw.get("team") or {}).get("id"))),
        player=names[0] if names else None,
        related_player=names[1] if len(names) > 1 else None,
    )


def normalize_match_details(data: dict[str, Any]) -> MatchDetailsDTO:
    competition = ((data.get("header") or {}).get("competitions") or [{}])[0]
    sides: dict[str, Side] = {
        str(c.get("id")): c["homeAway"]
        for c in competition.get("competitors") or []
        if c.get("homeAway") in ("home", "away")
    }
    lineups = [lu for r in data.get("rosters") or [] if (lu := normalize_lineup(r))]
    incidents = [i for raw in data.get("keyEvents") or [] if (i := normalize_incident(raw, sides))]
    return MatchDetailsDTO(
        lineups=sorted(lineups, key=lambda lu: lu.side != "home"),
        incidents=incidents,
        stats=normalize_match_stats(data.get("boxscore") or {}),
        attendance=_int((data.get("gameInfo") or {}).get("attendance")) or None,
    )


def normalize_team(raw: dict[str, Any]) -> TeamDTO:
    team = raw.get("team", raw)
    return TeamDTO(**team_ref(team).model_dump(), country=COUNTRY)


class EspnSoccerAdapter(HttpFixtureAdapter):
    sport_slug = "football"
    sport_name = "Futbol"
    source = "espn"
    default_competitions = tuple(LEAGUES)
    fixtures_subdir = "espn"
    base_url = BASE_URL
    # Opt-in switch instead of a key: unofficial endpoint, personal use only.
    requires_api_key = True
    scores_delayed = True

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        super().__init__(
            settings,
            api_key=ENABLED_MARKER if settings.espn_enabled else "",
            headers={"User-Agent": USER_AGENT},
            min_interval=MIN_REQUEST_INTERVAL_SECONDS,
            client=client,
        )

    def shift_fixture_dates(self, data: dict[str, Any], delta: timedelta) -> None:
        for event in data.get("events") or []:
            moved = parse_time(event["date"]) + delta
            event["date"] = moved.strftime("%Y-%m-%dT%H:%MZ")

    async def _scoreboard(self, league: str, month: str | None = None) -> dict[str, Any]:
        params = {"dates": month} if month else None
        return await self._request(
            f"/site/v2/sports/soccer/{league}/scoreboard", f"scoreboard_{league}", params
        )

    async def fetch_competitions(self) -> list[CompetitionDTO]:
        comps = []
        for league, name in LEAGUES.items():
            data = await self._scoreboard(league)
            info = (data.get("leagues") or [{}])[0]
            season = info.get("season") or {}
            year = _int(season.get("year")) or datetime.now(UTC).year
            logos = info.get("logos") or []
            comps.append(
                CompetitionDTO(
                    external_id=league,
                    name=name,
                    country=COUNTRY,
                    logo_url=logos[0].get("href") if logos else None,
                    season_key=str(year),
                    season_label=season_label(year),
                    season_start=date(year, SEASON_START_MONTH, 1),
                    season_end=date(year + 1, SEASON_START_MONTH - 1, 30),
                )
            )
        return comps

    async def fetch_events(self, competition_ext_id: str, season: str) -> list[EventDTO]:
        if self.use_fixtures:
            pages = [await self._scoreboard(competition_ext_id)]
        else:
            pages = [
                await self._scoreboard(competition_ext_id, month)
                for month in season_months(int(season))
            ]
        events: dict[str, EventDTO] = {}
        for page in pages:
            for raw in page.get("events") or []:
                event = normalize_event(raw)
                events[event.external_id] = event
        return sorted(events.values(), key=lambda e: e.start_time)

    async def fetch_standings(self, competition_ext_id: str, season: str) -> list[StandingDTO]:
        data = await self._request(
            f"/v2/sports/soccer/{competition_ext_id}/standings",
            f"standings_{competition_ext_id}",
            {"season": season},
        )
        groups = data.get("children") or []
        entries = groups[0].get("standings", {}).get("entries", []) if groups else []
        return sorted((normalize_standing(e) for e in entries), key=lambda r: r.position)

    async def fetch_match_details(
        self, competition_ext_id: str, event_ext_id: str
    ) -> MatchDetailsDTO | None:
        if self.use_fixtures and not self._has_fixture(f"summary_{event_ext_id}"):
            return None
        data = await self._request(
            f"/site/v2/sports/soccer/{competition_ext_id}/summary",
            f"summary_{event_ext_id}",
            {"event": event_ext_id},
        )
        return normalize_match_details(data)

    async def fetch_teams(self, competition_ext_id: str, season: str) -> list[TeamDTO]:
        data = await self._request(
            f"/site/v2/sports/soccer/{competition_ext_id}/teams",
            f"teams_{competition_ext_id}",
        )
        leagues = (data.get("sports") or [{}])[0].get("leagues") or [{}]
        return [normalize_team(t) for t in leagues[0].get("teams") or []]
