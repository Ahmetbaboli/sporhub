"""Read-side use cases: query repositories, map to response models, cache hot paths."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cached
from app.core.errors import AppError, NotFoundError
from app.models import Competition, Event, Player, Standing, Team
from app.repositories import queries
from app.schemas.api import (
    CompetitionDetail,
    CompetitionOut,
    EventOut,
    Page,
    ParticipantOut,
    PlayerOut,
    SearchResults,
    SeasonOut,
    SportOut,
    StandingOut,
    TeamDetail,
    TeamOut,
)

MIN_SEARCH_LENGTH = 2
DEFAULT_TZ = "UTC"


class SportList(Page[SportOut]):
    pass


# ---- mappers -------------------------------------------------------------------------


def team_out(team: Team) -> TeamOut:
    return TeamOut(
        id=team.id,
        name=team.name,
        short_name=team.short_name,
        logo_url=team.logo_url,
        country=team.country,
        sport_slug=team.sport.slug if "sport" in team.__dict__ else None,
    )


def player_out(player: Player) -> PlayerOut:
    team = player.__dict__.get("team")
    return PlayerOut(
        id=player.id,
        name=player.name,
        position=player.position,
        nationality=player.nationality,
        team=team_out(team) if team else None,
        extra=player.extra or {},
    )


def competition_out(comp: Competition) -> CompetitionOut:
    return CompetitionOut(
        id=comp.id,
        slug=comp.slug,
        name=comp.name,
        sport_slug=comp.sport.slug,
        country=comp.country,
        logo_url=comp.logo_url,
    )


def event_out(event: Event) -> EventOut:
    return EventOut(
        id=event.id,
        kind=event.kind,
        name=event.name,
        start_time=event.start_time,
        status=event.status,
        venue=event.venue,
        round=event.round,
        competition=competition_out(event.season.competition),
        season=event.season.year_label,
        participants=[
            ParticipantOut(
                team=team_out(p.team) if p.team else None,
                player=player_out(p.player) if p.player else None,
                side=p.side,
                score=p.score,
                position=p.position,
                points=p.points,
                extra=p.extra or {},
            )
            for p in event.participants
        ],
        extra=event.extra or {},
    )


def standing_out(row: Standing) -> StandingOut:
    return StandingOut(
        position=row.position,
        team=team_out(row.team) if row.team else None,
        player=player_out(row.player) if row.player else None,
        played=row.played,
        won=row.won,
        drawn=row.drawn,
        lost=row.lost,
        points=row.points,
        extra=row.extra or {},
    )


# ---- cached response wrappers (Pydantic models so Redis can round-trip them) ----------


class EventList(Page[EventOut]):
    pass


class StandingList(Page[StandingOut]):
    pass


class CompetitionList(Page[CompetitionOut]):
    pass


class TodayEvents(Page[EventOut]):
    pass


def _page(items: list, page: int, page_size: int, total: int | None = None) -> dict:
    return {
        "items": items,
        "total": len(items) if total is None else total,
        "page": page,
        "page_size": page_size,
    }


# ---- use cases --------------------------------------------------------------------------


async def get_sports(session: AsyncSession) -> SportList:
    async def load() -> SportList:
        sports = [SportOut.model_validate(s) for s in await queries.list_sports(session)]
        return SportList(**_page(sports, 1, max(len(sports), 1)))

    return await cached("sports", SportList, load)


async def get_competitions(session: AsyncSession, sport_slug: str) -> CompetitionList:
    async def load() -> CompetitionList:
        if not await queries.sport_exists(session, sport_slug):
            raise NotFoundError("Spor")
        comps = [competition_out(c) for c in await queries.list_competitions(session, sport_slug)]
        return CompetitionList(**_page(comps, 1, max(len(comps), 1)))

    return await cached(f"competitions:{sport_slug}", CompetitionList, load)


async def _require_competition(session: AsyncSession, ref: str) -> Competition:
    comp = await queries.get_competition(session, ref)
    if comp is None:
        raise NotFoundError("Lig")
    return comp


async def get_competition_detail(session: AsyncSession, ref: str) -> CompetitionDetail:
    async def load() -> CompetitionDetail:
        comp = await _require_competition(session, ref)
        season = await queries.current_season(session, comp.id)
        return CompetitionDetail(
            **competition_out(comp).model_dump(),
            current_season=SeasonOut.model_validate(season) if season else None,
        )

    return await cached(f"competition:{ref}", CompetitionDetail, load)


async def get_competition_events(
    session: AsyncSession,
    ref: str,
    *,
    status: list[str] | None,
    start: datetime | None,
    end: datetime | None,
    descending: bool,
    page: int,
    page_size: int,
) -> EventList:
    async def load() -> EventList:
        comp = await _require_competition(session, ref)
        rows, total = await queries.list_competition_events(
            session,
            comp.id,
            status=status,
            start=start,
            end=end,
            descending=descending,
            page=page,
            page_size=page_size,
        )
        return EventList(**_page([event_out(e) for e in rows], page, page_size, total))

    key = f"cevents:{ref}:{status}:{start}:{end}:{descending}:{page}:{page_size}"
    return await cached(key, EventList, load)


async def get_competition_standings(session: AsyncSession, ref: str) -> StandingList:
    async def load() -> StandingList:
        comp = await _require_competition(session, ref)
        season = await queries.current_season(session, comp.id)
        rows = await queries.list_standings(session, season.id) if season else []
        return StandingList(**_page([standing_out(r) for r in rows], 1, max(len(rows), 1)))

    return await cached(f"standings:{ref}", StandingList, load)


def local_day_bounds(day: date | None, tz_name: str) -> tuple[datetime, datetime]:
    """UTC [start, end) of the calendar day `day` in timezone `tz_name`."""
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        raise AppError(422, "invalid_timezone", f"Geçersiz saat dilimi: {tz_name}") from None
    local_day = day or datetime.now(tz).date()
    start = datetime.combine(local_day, time.min, tzinfo=tz)
    return start, start + timedelta(days=1)


async def get_today_events(
    session: AsyncSession, sport_slug: str | None, day: date | None, tz_name: str
) -> TodayEvents:
    start, end = local_day_bounds(day, tz_name)

    async def load() -> TodayEvents:
        rows = await queries.list_events_between(session, start, end, sport_slug)
        return TodayEvents(**_page([event_out(e) for e in rows], 1, max(len(rows), 1)))

    return await cached(f"today:{sport_slug}:{start.isoformat()}", TodayEvents, load, ttl=30)


async def get_event_detail(session: AsyncSession, event_id: int) -> EventOut:
    event = await queries.get_event(session, event_id)
    if event is None:
        raise NotFoundError("Etkinlik")
    return event_out(event)


async def get_team_detail(session: AsyncSession, team_id: int) -> TeamDetail:
    team = await queries.get_team(session, team_id)
    if team is None:
        raise NotFoundError("Takım")
    squad = await queries.list_squad(session, team_id)
    return TeamDetail(**team_out(team).model_dump(), squad=[player_out(p) for p in squad])


async def get_team_events(
    session: AsyncSession, team_id: int, page: int, page_size: int, descending: bool
) -> EventList:
    if await queries.get_team(session, team_id) is None:
        raise NotFoundError("Takım")
    rows, total = await queries.list_team_events(session, team_id, page, page_size, descending)
    return EventList(**_page([event_out(e) for e in rows], page, page_size, total))


async def get_player_detail(session: AsyncSession, player_id: int) -> PlayerOut:
    player = await queries.get_player(session, player_id)
    if player is None:
        raise NotFoundError("Oyuncu")
    return player_out(player)


async def search_all(session: AsyncSession, query: str) -> SearchResults:
    q = query.strip()
    if len(q) < MIN_SEARCH_LENGTH:
        raise AppError(422, "query_too_short", f"En az {MIN_SEARCH_LENGTH} karakter girin.")

    async def load() -> SearchResults:
        comps, teams, players = await queries.search(session, q)
        return SearchResults(
            query=q,
            competitions=[competition_out(c) for c in comps],
            teams=[team_out(t) for t in teams],
            players=[player_out(p) for p in players],
        )

    return await cached(f"search:{q.lower()}", SearchResults, load, ttl=120)
