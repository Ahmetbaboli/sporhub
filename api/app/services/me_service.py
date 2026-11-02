"""Favorites and the personal dashboard. Every function is scoped to one user id."""

from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.errors import AppError, NotFoundError
from app.db.dialect import insert_for
from app.models import Competition, Favorite, Player, Team, User
from app.repositories import queries
from app.schemas.api import SeasonOut
from app.schemas.me import (
    CompetitionPlace,
    Dashboard,
    FavoriteIds,
    Favorites,
    TeamActivity,
)
from app.services.read_service import (
    competition_out,
    event_out,
    player_out,
    standing_out,
    team_out,
)

FavoriteKind = Literal["teams", "players", "competitions"]
MAX_FAVORITES_PER_USER = 200
DASHBOARD_EVENTS_PER_TEAM = 3
DASHBOARD_TABLE_ROWS = 5

_COLUMN = {"teams": "team_id", "players": "player_id", "competitions": "competition_id"}
_MODEL = {"teams": Team, "players": Player, "competitions": Competition}


async def _ids(session: AsyncSession, user_id: int) -> FavoriteIds:
    rows = (
        await session.execute(
            select(Favorite.team_id, Favorite.player_id, Favorite.competition_id)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc(), Favorite.id.desc())
        )
    ).all()
    return FavoriteIds(
        teams=[r[0] for r in rows if r[0] is not None],
        players=[r[1] for r in rows if r[1] is not None],
        competitions=[r[2] for r in rows if r[2] is not None],
    )


async def favorite_ids(session: AsyncSession, user_id: int) -> FavoriteIds:
    return await _ids(session, user_id)


async def add_favorite(
    session: AsyncSession, user_id: int, kind: FavoriteKind, entity_id: int
) -> None:
    if await session.get(_MODEL[kind], entity_id) is None:
        raise NotFoundError("Kayıt")
    count = await session.scalar(
        select(func.count()).select_from(Favorite).where(Favorite.user_id == user_id)
    )
    if (count or 0) >= MAX_FAVORITES_PER_USER:
        raise AppError(
            409, "favorite_limit", f"En fazla {MAX_FAVORITES_PER_USER} favori eklenebilir."
        )
    column = _COLUMN[kind]
    stmt = (
        insert_for(session)(Favorite)
        .values(user_id=user_id, created_at=datetime.now(UTC), **{column: entity_id})
        .on_conflict_do_nothing(index_elements=["user_id", column])  # idempotent PUT
    )
    await session.execute(stmt)
    await session.commit()


async def remove_favorite(
    session: AsyncSession, user_id: int, kind: FavoriteKind, entity_id: int
) -> None:
    column = getattr(Favorite, _COLUMN[kind])
    # Scoped by user_id: ids of other users' favorites can never be touched.
    await session.execute(delete(Favorite).where(Favorite.user_id == user_id, column == entity_id))
    await session.commit()


async def list_favorites(session: AsyncSession, user_id: int) -> Favorites:
    ids = await _ids(session, user_id)
    teams = await _load(session, Team, ids.teams, joinedload(Team.sport))
    players = await _load(
        session, Player, ids.players, joinedload(Player.team).joinedload(Team.sport)
    )
    comps = await _load(session, Competition, ids.competitions, joinedload(Competition.sport))
    return Favorites(
        teams=[team_out(t) for t in teams],
        players=[player_out(p) for p in players],
        competitions=[competition_out(c) for c in comps],
    )


async def _load(session, model, ids: list[int], *options):
    if not ids:
        return []
    rows = (
        await session.scalars(select(model).where(model.id.in_(ids)).options(*options))
    ).unique()
    by_id = {row.id: row for row in rows}
    return [by_id[i] for i in ids if i in by_id]  # keep newest-first order


async def dashboard(session: AsyncSession, user_id: int) -> Dashboard:
    favorites = await list_favorites(session, user_id)
    teams = [await _team_activity(session, t.id, t) for t in favorites.teams]
    places = [await _competition_place(session, c.id, c, favorites) for c in favorites.competitions]
    return Dashboard(teams=teams, competitions=places)


async def _team_activity(session: AsyncSession, team_id: int, team) -> TeamActivity:
    recent, _ = await queries.list_team_events(
        session, team_id, 1, DASHBOARD_EVENTS_PER_TEAM, True, ["finished"]
    )
    upcoming, _ = await queries.list_team_events(
        session, team_id, 1, DASHBOARD_EVENTS_PER_TEAM, False, ["scheduled", "live"]
    )
    return TeamActivity(
        team=team, recent=[event_out(e) for e in recent], upcoming=[event_out(e) for e in upcoming]
    )


async def _competition_place(
    session: AsyncSession, competition_id: int, competition, favorites: Favorites
) -> CompetitionPlace:
    season = await queries.current_season(session, competition_id)
    rows = await queries.list_standings(session, season.id) if season else []
    team_ids = {t.id for t in favorites.teams}
    player_ids = {p.id for p in favorites.players}
    mine = [
        r
        for r in rows
        if (r.team_id in team_ids and r.player_id is None) or r.player_id in player_ids
    ]
    # F1-style tables hold driver rows and constructor rows; the "top" is the driver table.
    top_pool = [r for r in rows if r.player_id] or rows
    return CompetitionPlace(
        competition=competition,
        season=SeasonOut.model_validate(season) if season else None,
        table=[standing_out(r) for r in top_pool[:DASHBOARD_TABLE_ROWS]],
        mine=[standing_out(r) for r in mine],
    )


async def delete_account(session: AsyncSession, user_id: int) -> None:
    """Remove the user and everything stored about them (favorites). Irreversible."""
    await session.execute(delete(Favorite).where(Favorite.user_id == user_id))
    await session.execute(delete(User).where(User.id == user_id))
    await session.commit()
