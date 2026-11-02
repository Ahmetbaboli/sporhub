"""Read-side SQL. Returns ORM rows with everything the mappers need already loaded."""

from datetime import datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload, selectinload

from app.models import (
    Competition,
    Event,
    EventParticipant,
    Player,
    Season,
    Sport,
    Standing,
    Team,
)

SEARCH_LIMIT = 10


def _event_base() -> Select[tuple[Event]]:
    """Events joined to season/competition/sport, without loader options (safe to count)."""
    return select(Event).join(Event.season).join(Season.competition).join(Competition.sport)


def _with_loading(stmt: Select[tuple[Event]]) -> Select[tuple[Event]]:
    return stmt.options(
        contains_eager(Event.season)
        .contains_eager(Season.competition)
        .contains_eager(Competition.sport),
        selectinload(Event.participants).options(
            joinedload(EventParticipant.team).joinedload(Team.sport),
            joinedload(EventParticipant.player),
        ),
    )


def _event_select() -> Select[tuple[Event]]:
    return _with_loading(_event_base())


async def list_sports(session: AsyncSession) -> list[Sport]:
    return list((await session.scalars(select(Sport).order_by(Sport.id))).all())


async def list_competitions(session: AsyncSession, sport_slug: str) -> list[Competition]:
    stmt = (
        select(Competition)
        .join(Competition.sport)
        .options(contains_eager(Competition.sport))
        .where(Sport.slug == sport_slug)
        .order_by(Competition.id)
    )
    return list((await session.scalars(stmt)).all())


async def sport_exists(session: AsyncSession, slug: str) -> bool:
    return bool(
        await session.scalar(select(func.count()).select_from(Sport).where(Sport.slug == slug))
    )


async def get_competition(session: AsyncSession, ref: str) -> Competition | None:
    """`ref` is a numeric id or a slug."""
    cond = Competition.id == int(ref) if ref.isdigit() else Competition.slug == ref
    stmt = (
        select(Competition)
        .join(Competition.sport)
        .options(contains_eager(Competition.sport))
        .where(cond)
    )
    return (await session.scalars(stmt)).first()


async def current_season(session: AsyncSession, competition_id: int) -> Season | None:
    stmt = (
        select(Season)
        .where(Season.competition_id == competition_id)
        .order_by(Season.is_current.desc(), Season.year_label.desc())
    )
    return (await session.scalars(stmt)).first()


async def list_competition_events(
    session: AsyncSession,
    competition_id: int,
    *,
    status: list[str] | None,
    start: datetime | None,
    end: datetime | None,
    descending: bool,
    page: int,
    page_size: int,
) -> tuple[list[Event], int]:
    stmt = _event_base().where(Season.competition_id == competition_id, Season.is_current)
    if status:
        stmt = stmt.where(Event.status.in_(status))
    if start:
        stmt = stmt.where(Event.start_time >= start)
    if end:
        stmt = stmt.where(Event.start_time < end)
    return await _paginate_events(session, stmt, descending, page, page_size)


async def _paginate_events(
    session: AsyncSession, stmt: Select[tuple[Event]], descending: bool, page: int, page_size: int
) -> tuple[list[Event], int]:
    """`stmt` must come from _event_base() (no loader options) plus filters."""
    count_stmt = select(func.count()).select_from(stmt.with_only_columns(Event.id).subquery())
    total = await session.scalar(count_stmt)
    order = Event.start_time.desc() if descending else Event.start_time.asc()
    page_stmt = _with_loading(stmt).order_by(order, Event.id)
    page_stmt = page_stmt.offset((page - 1) * page_size).limit(page_size)
    return list((await session.scalars(page_stmt)).unique().all()), total or 0


async def list_events_between(
    session: AsyncSession, start: datetime, end: datetime, sport_slug: str | None
) -> list[Event]:
    stmt = _event_select().where(Event.start_time >= start, Event.start_time < end)
    if sport_slug:
        stmt = stmt.where(Sport.slug == sport_slug)
    stmt = stmt.order_by(Competition.id, Event.start_time, Event.id)
    return list((await session.scalars(stmt)).unique().all())


async def get_event(session: AsyncSession, event_id: int) -> Event | None:
    return (await session.scalars(_event_select().where(Event.id == event_id))).unique().first()


async def list_team_events(
    session: AsyncSession,
    team_id: int,
    page: int,
    page_size: int,
    descending: bool,
    statuses: list[str] | None = None,
) -> tuple[list[Event], int]:
    involved = select(EventParticipant.event_id).where(EventParticipant.team_id == team_id)
    stmt = _event_base().where(Event.id.in_(involved))
    if statuses:
        stmt = stmt.where(Event.status.in_(statuses))
    return await _paginate_events(session, stmt, descending, page, page_size)


async def list_finished_matches(
    session: AsyncSession, team_id: int, limit: int, opponent_id: int | None = None
) -> list[Event]:
    """Finished matches of a team (optionally only against `opponent_id`), newest first."""
    involved = select(EventParticipant.event_id).where(EventParticipant.team_id == team_id)
    stmt = _event_select().where(
        Event.id.in_(involved), Event.status == "finished", Event.kind == "match"
    )
    if opponent_id is not None:
        against = select(EventParticipant.event_id).where(EventParticipant.team_id == opponent_id)
        stmt = stmt.where(Event.id.in_(against))
    stmt = stmt.order_by(Event.start_time.desc(), Event.id.desc()).limit(limit)
    return list((await session.scalars(stmt)).unique().all())


async def list_player_events(
    session: AsyncSession, player_id: int, page: int, page_size: int, descending: bool
) -> tuple[list[Event], int]:
    involved = select(EventParticipant.event_id).where(EventParticipant.player_id == player_id)
    stmt = _event_base().where(Event.id.in_(involved))
    return await _paginate_events(session, stmt, descending, page, page_size)


async def list_teams(
    session: AsyncSession, sport_slug: str | None, q: str | None, limit: int
) -> list[Team]:
    stmt = select(Team).join(Team.sport).options(contains_eager(Team.sport))
    if sport_slug:
        stmt = stmt.where(Sport.slug == sport_slug)
    if q:
        stmt = stmt.where(Team.name.ilike(_like(q)))
    return list((await session.scalars(stmt.order_by(Team.name).limit(limit))).all())


async def list_players(
    session: AsyncSession, sport_slug: str | None, q: str | None, limit: int
) -> list[Player]:
    stmt = (
        select(Player)
        .join(Player.sport)
        .options(contains_eager(Player.sport), joinedload(Player.team).joinedload(Team.sport))
    )
    if sport_slug:
        stmt = stmt.where(Sport.slug == sport_slug)
    if q:
        stmt = stmt.where(Player.name.ilike(_like(q)))
    return list((await session.scalars(stmt.order_by(Player.name).limit(limit))).unique().all())


def _like(text: str) -> str:
    return f"%{text.replace('%', '').replace('_', '')}%"


async def standings_of(
    session: AsyncSession, *, team_id: int | None = None, player_id: int | None = None
) -> list[tuple[Standing, Season, Competition]]:
    """A team's (or player's) row in the current season table of every competition."""
    stmt = (
        select(Standing, Season, Competition)
        .join(Season, Standing.season_id == Season.id)
        .join(Competition, Season.competition_id == Competition.id)
        .join(Competition.sport)
        .options(
            contains_eager(Competition.sport),
            joinedload(Standing.team).joinedload(Team.sport),
            joinedload(Standing.player),
        )
        .where(Season.is_current)
        .order_by(Competition.id)
    )
    if player_id is not None:
        stmt = stmt.where(Standing.player_id == player_id)
    else:
        # A team's own row (constructor/club), not the driver rows that merely list the team.
        stmt = stmt.where(Standing.team_id == team_id, Standing.player_id.is_(None))
    rows = (await session.execute(stmt)).unique().all()
    return [(r[0], r[1], r[2]) for r in rows]


async def list_standings(session: AsyncSession, season_id: int) -> list[Standing]:
    stmt = (
        select(Standing)
        .where(Standing.season_id == season_id)
        .options(joinedload(Standing.team).joinedload(Team.sport), joinedload(Standing.player))
        .order_by(Standing.position)
    )
    return list((await session.scalars(stmt)).unique().all())


async def get_team(session: AsyncSession, team_id: int) -> Team | None:
    stmt = select(Team).where(Team.id == team_id).options(joinedload(Team.sport))
    return (await session.scalars(stmt)).first()


async def list_squad(session: AsyncSession, team_id: int) -> list[Player]:
    stmt = select(Player).where(Player.team_id == team_id).order_by(Player.id)
    return list((await session.scalars(stmt)).all())


async def get_player(session: AsyncSession, player_id: int) -> Player | None:
    stmt = (
        select(Player)
        .where(Player.id == player_id)
        .options(joinedload(Player.team).joinedload(Team.sport))
    )
    return (await session.scalars(stmt)).first()


async def search(
    session: AsyncSession, query: str
) -> tuple[list[Competition], list[Team], list[Player]]:
    like = _like(query)
    comps = await session.scalars(
        select(Competition)
        .join(Competition.sport)
        .options(contains_eager(Competition.sport))
        .where(or_(Competition.name.ilike(like), Competition.country.ilike(like)))
        .order_by(Competition.name)
        .limit(SEARCH_LIMIT)
    )
    teams = await session.scalars(
        select(Team)
        .options(joinedload(Team.sport))
        .where(or_(Team.name.ilike(like), Team.short_name.ilike(like)))
        .order_by(Team.name)
        .limit(SEARCH_LIMIT)
    )
    players = await session.scalars(
        select(Player)
        .options(joinedload(Player.team).joinedload(Team.sport))
        .where(Player.name.ilike(like))
        .order_by(Player.name)
        .limit(SEARCH_LIMIT)
    )
    return list(comps.all()), list(teams.all()), list(players.all())
