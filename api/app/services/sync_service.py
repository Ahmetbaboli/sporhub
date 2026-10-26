"""Writes adapter DTOs to the database. Idempotent: re-running never duplicates rows."""

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.base import BaseAdapter
from app.adapters.dto import (
    CompetitionDTO,
    EventDTO,
    StandingDTO,
    TeamDTO,
    TeamRef,
)
from app.core.cache import invalidate_all
from app.models import (
    Competition,
    Event,
    EventParticipant,
    Player,
    Season,
    Sport,
    Standing,
    SyncRun,
    Team,
)
from app.repositories.upsert import upsert_row

logger = logging.getLogger(__name__)

STATUS_RUNNING = "running"
STATUS_SUCCESS = "success"
STATUS_PARTIAL = "partial"
STATUS_FAILED = "failed"
MAX_ERROR_LENGTH = 2000


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


@dataclass
class SyncContext:
    """Per-run state: counters plus an external_id -> id cache for teams and players."""

    session: AsyncSession
    adapter: BaseAdapter
    sport_id: int
    upserted: int = 0
    team_ids: dict[str, int] = field(default_factory=dict)
    player_ids: dict[str, int] = field(default_factory=dict)


async def ensure_sport(session: AsyncSession, slug: str, name: str) -> int:
    existing = await session.scalar(select(Sport.id).where(Sport.slug == slug))
    if existing is not None:
        return existing
    return await upsert_row(session, Sport, {"slug": slug, "name": name}, ["slug"])


async def _upsert_competition(ctx: SyncContext, dto: CompetitionDTO) -> int:
    return await upsert_row(
        ctx.session,
        Competition,
        {
            "sport_id": ctx.sport_id,
            "source": ctx.adapter.source,
            "external_id": dto.external_id,
            "slug": slugify(dto.name),
            "name": dto.name,
            "country": dto.country,
            "logo_url": dto.logo_url,
        },
        ["source", "external_id"],
    )


async def _upsert_season(ctx: SyncContext, competition_id: int, dto: CompetitionDTO) -> int | None:
    if not dto.season_label:
        return None
    await ctx.session.execute(
        update(Season).where(Season.competition_id == competition_id).values(is_current=False)
    )
    return await upsert_row(
        ctx.session,
        Season,
        {
            "competition_id": competition_id,
            "year_label": dto.season_label,
            "start_date": dto.season_start,
            "end_date": dto.season_end,
            "is_current": True,
        },
        ["competition_id", "year_label"],
    )


async def _upsert_team(ctx: SyncContext, ref: TeamRef, country: str | None = None) -> int:
    team_id = await upsert_row(
        ctx.session,
        Team,
        {
            "sport_id": ctx.sport_id,
            "source": ctx.adapter.source,
            "external_id": ref.external_id,
            "name": ref.name,
            "short_name": ref.short_name,
            "logo_url": ref.logo_url,
            "country": country,
        },
        ["source", "external_id"],
    )
    ctx.team_ids[ref.external_id] = team_id
    ctx.upserted += 1
    return team_id


async def _team_id(ctx: SyncContext, ref: TeamRef) -> int:
    """Resolve a team referenced by an event/standing, creating a stub if the roster lacks it."""
    if ref.external_id in ctx.team_ids:
        return ctx.team_ids[ref.external_id]
    existing = await ctx.session.scalar(
        select(Team.id).where(
            Team.source == ctx.adapter.source, Team.external_id == ref.external_id
        )
    )
    if existing is not None:
        ctx.team_ids[ref.external_id] = existing
        return existing
    return await _upsert_team(ctx, ref)


async def _upsert_teams(ctx: SyncContext, teams: list[TeamDTO]) -> None:
    for dto in teams:
        team_id = await _upsert_team(ctx, dto, dto.country)
        for player in dto.squad:
            player_id = await upsert_row(
                ctx.session,
                Player,
                {
                    "sport_id": ctx.sport_id,
                    "source": ctx.adapter.source,
                    "external_id": player.external_id,
                    "name": player.name,
                    "position": player.position,
                    "nationality": player.nationality,
                    "team_id": team_id,
                    "extra": player.extra,
                },
                ["source", "external_id"],
            )
            ctx.player_ids[player.external_id] = player_id
            ctx.upserted += 1


async def _participants(ctx: SyncContext, dto: EventDTO) -> list[EventParticipant]:
    rows = []
    for p in dto.participants:
        rows.append(
            EventParticipant(
                team_id=await _team_id(ctx, p.team) if p.team else None,
                player_id=ctx.player_ids.get(p.player_external_id or ""),
                side=p.side,
                score=p.score,
                position=p.position,
                points=p.points,
                extra=p.extra,
            )
        )
    return rows


async def _upsert_events(ctx: SyncContext, season_id: int, events: list[EventDTO]) -> None:
    for dto in events:
        event_id = await upsert_row(
            ctx.session,
            Event,
            {
                "season_id": season_id,
                "source": ctx.adapter.source,
                "external_id": dto.external_id,
                "kind": dto.kind,
                "name": dto.name,
                "start_time": dto.start_time,
                "status": dto.status,
                "venue": dto.venue,
                "round": dto.round,
                "extra": dto.extra,
            },
            ["source", "external_id"],
        )
        await ctx.session.execute(
            delete(EventParticipant).where(EventParticipant.event_id == event_id)
        )
        for row in await _participants(ctx, dto):
            row.event_id = event_id
            ctx.session.add(row)
        ctx.upserted += 1


async def _replace_standings(
    ctx: SyncContext, season_id: int, standings: list[StandingDTO]
) -> None:
    if not standings:
        return
    await ctx.session.execute(delete(Standing).where(Standing.season_id == season_id))
    for dto in standings:
        ctx.session.add(
            Standing(
                season_id=season_id,
                team_id=await _team_id(ctx, dto.team) if dto.team else None,
                player_id=ctx.player_ids.get(dto.player_external_id or ""),
                position=dto.position,
                played=dto.played,
                won=dto.won,
                drawn=dto.drawn,
                lost=dto.lost,
                points=dto.points,
                extra=dto.extra,
            )
        )
        ctx.upserted += 1


async def _sync_competition(ctx: SyncContext, dto: CompetitionDTO) -> None:
    competition_id = await _upsert_competition(ctx, dto)
    ctx.upserted += 1
    season_id = await _upsert_season(ctx, competition_id, dto)
    if season_id is None or dto.season_key is None:
        return
    ext, season = dto.external_id, dto.season_key
    await _upsert_teams(ctx, await ctx.adapter.fetch_teams(ext, season))
    await _upsert_events(ctx, season_id, await ctx.adapter.fetch_events(ext, season))
    await _replace_standings(ctx, season_id, await ctx.adapter.fetch_standings(ext, season))


async def run_sync(
    maker: async_sessionmaker[AsyncSession],
    adapter: BaseAdapter,
    competitions: tuple[str, ...] | None = None,
) -> SyncRun:
    """Sync every wanted competition of `adapter`; a failing competition does not stop the rest."""
    wanted = set(competitions or adapter.default_competitions)
    async with maker() as session:
        run = SyncRun(adapter=adapter.source, started_at=datetime.now(UTC), status=STATUS_RUNNING)
        session.add(run)
        await session.commit()
        run_id = run.id
        sport_id = await ensure_sport(session, adapter.sport_slug, adapter.sport_name)
        await session.commit()  # a later per-competition rollback must not undo the sport row
        ctx = SyncContext(session=session, adapter=adapter, sport_id=sport_id)
        errors: list[str] = []
        try:
            targets = [c for c in await adapter.fetch_competitions() if c.external_id in wanted]
        except Exception as exc:
            targets, errors = [], [f"fetch_competitions: {exc}"]
        for dto in targets:
            try:
                await _sync_competition(ctx, dto)
                await session.commit()
            except Exception as exc:
                await session.rollback()
                logger.exception("competition sync failed", extra={"competition": dto.external_id})
                errors.append(f"{dto.external_id}: {exc}")
        run = await session.get(SyncRun, run_id) or run  # reload: rollbacks expire it
        run.finished_at = datetime.now(UTC)
        run.items_upserted = ctx.upserted
        run.error = "; ".join(errors)[:MAX_ERROR_LENGTH] or None
        run.status = (
            STATUS_SUCCESS if not errors else STATUS_PARTIAL if ctx.upserted else STATUS_FAILED
        )
        session.add(run)
        await session.commit()
        logger.info(
            "sync finished",
            extra={"adapter": adapter.source, "status": run.status, "items": run.items_upserted},
        )
    await invalidate_all()
    return run
