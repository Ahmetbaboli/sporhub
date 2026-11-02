"""News: sync from feeds (upsert + entity tagging), manual entries and read queries."""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import joinedload, selectinload

from app.adapters.news_rss import SOURCE_PREFIX, NewsDTO, RssNewsAdapter
from app.core.cache import cached, invalidate_all
from app.core.errors import NotFoundError
from app.models import Competition, NewsArticle, NewsTag, Player, Sport, SyncRun, Team
from app.repositories.upsert import upsert_row
from app.schemas.news import ArchiveMonth, NewsArchive, NewsList, NewsOut, NewsTagOut
from app.services.sync_service import (
    MAX_ERROR_LENGTH,
    STATUS_FAILED,
    STATUS_PARTIAL,
    STATUS_RUNNING,
    STATUS_SUCCESS,
)

logger = logging.getLogger(__name__)

MAX_TAGS_PER_ARTICLE = 10
MIN_ALIAS_LENGTH = 4
# Club-name decorations that are often dropped in headlines ("Chelsea FC" -> "Chelsea").
CLUB_AFFIXES = re.compile(r"^(?:FC|AFC|CF|SK|FK|AC|AS|SS|US|SC|1\.)\s+|\s+(?:FC|AFC|CF|SK|FK)$")
MANUAL_SOURCE = "manual"


@dataclass(frozen=True)
class _Target:
    """An alias pattern. Several candidates = a shared player name, resolved by team."""

    kind: str  # "team_id" | "player_id" | "competition_id"
    candidates: tuple[tuple[int, int | None], ...]  # (entity id, player's team id)
    pattern: re.Pattern[str]


def _pattern(alias: str) -> re.Pattern[str]:
    return re.compile(rf"(?<!\w){re.escape(alias)}(?!\w)", re.IGNORECASE)


def _aliases(kind: str, name: str, short_name: str | None = None) -> set[str]:
    names = {name}
    if kind == "team_id":
        names.add(CLUB_AFFIXES.sub("", name).strip())
        if short_name:
            names.add(short_name)
    if kind == "player_id" and " " not in name.strip():
        return set()  # single-word player names match far too much
    return {n for n in names if len(n) >= MIN_ALIAS_LENGTH}


Entity = tuple[str, int, str, str | None, int | None]  # kind, id, name, short, team


def build_targets(entities: list[Entity]) -> list[_Target]:
    """One pattern per alias. A team/competition alias shared by two entities is dropped; a
    shared player name is kept with all candidates and resolved by the teams in the text."""
    owners: dict[tuple[str, str], dict[int, int | None]] = defaultdict(dict)
    for kind, entity_id, name, short, team_id in entities:
        for alias in _aliases(kind, name, short):
            owners[(kind, alias.casefold())][entity_id] = team_id
    targets = []
    for (kind, alias), ids in owners.items():
        if len(ids) == 1 or kind == "player_id":
            targets.append(_Target(kind, tuple(ids.items()), _pattern(alias)))
    return targets


def find_tags(text: str, targets: list[_Target]) -> list[tuple[str, int]]:
    found: list[tuple[str, int]] = []
    shared: list[_Target] = []
    for target in targets:
        if not target.pattern.search(text):
            continue
        if len(target.candidates) > 1:
            shared.append(target)
        elif (key := (target.kind, target.candidates[0][0])) not in found:
            found.append(key)
    teams = {entity_id for kind, entity_id in found if kind == "team_id"}
    for target in shared:  # "Jonas Demir" + "Chelsea" -> the Jonas Demir who plays for Chelsea
        matches = [pid for pid, team_id in target.candidates if team_id in teams]
        if len(matches) == 1 and (key := (target.kind, matches[0])) not in found:
            found.append(key)
    return found[:MAX_TAGS_PER_ARTICLE]


async def _load_targets(session: AsyncSession, sport_id: int | None) -> list[_Target]:
    def scoped(stmt, column):
        return stmt.where(column == sport_id) if sport_id else stmt

    teams = await session.execute(
        scoped(select(Team.id, Team.name, Team.short_name), Team.sport_id)
    )
    players = await session.execute(
        scoped(select(Player.id, Player.name, Player.team_id), Player.sport_id)
    )
    comps = await session.execute(
        scoped(select(Competition.id, Competition.name), Competition.sport_id)
    )
    entities: list[Entity] = [("team_id", i, n, s, None) for i, n, s in teams]
    entities += [("player_id", i, n, None, team) for i, n, team in players]
    entities += [("competition_id", i, n, None, None) for i, n in comps]
    return build_targets(entities)


class _Tagger:
    """Caches targets per sport for one sync run."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._cache: dict[int | None, list[_Target]] = {}

    async def tags(self, sport_id: int | None, text: str) -> list[tuple[str, int]]:
        if sport_id not in self._cache:
            self._cache[sport_id] = await _load_targets(self._session, sport_id)
        return find_tags(text, self._cache[sport_id])


async def _sport_ids(session: AsyncSession) -> dict[str, int]:
    return {slug: i for i, slug in await session.execute(select(Sport.id, Sport.slug))}


async def save_article(
    session: AsyncSession, dto: NewsDTO, sport_id: int | None, tagger: _Tagger
) -> int:
    """Upsert one article and rewrite its tags (idempotent)."""
    article_id = await upsert_row(
        session,
        NewsArticle,
        {
            "source": dto.source,
            "external_id": dto.external_id,
            "sport_id": sport_id,
            "url": dto.url,
            "title": dto.title,
            "summary": dto.summary,
            "image_url": dto.image_url,
            "author": dto.author,
            "published_at": dto.published_at,
            "category": dto.category,
            "is_breaking": dto.is_breaking,
            "language": dto.language,
        },
        ["source", "external_id"],
    )
    await session.execute(delete(NewsTag).where(NewsTag.article_id == article_id))
    for kind, entity_id in await tagger.tags(sport_id, f"{dto.title} {dto.summary}"):
        session.add(NewsTag(article_id=article_id, **{kind: entity_id}))
    return article_id


async def run_news_sync(
    maker: async_sessionmaker[AsyncSession], adapter: RssNewsAdapter
) -> SyncRun:
    async with maker() as session:
        run = SyncRun(adapter=adapter.source, started_at=datetime.now(UTC), status=STATUS_RUNNING)
        session.add(run)
        await session.commit()
        saved = 0
        errors: list[str] = []
        try:
            items = await adapter.fetch()
            errors.extend(adapter.errors)
            sports = await _sport_ids(session)
            tagger = _Tagger(session)
            for dto in items:
                await save_article(session, dto, sports.get(dto.sport_slug or ""), tagger)
                saved += 1
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.exception("news sync failed")
            errors.append(str(exc))
            saved = 0
        run = await session.get(SyncRun, run.id) or run
        run.finished_at = datetime.now(UTC)
        run.items_upserted = saved
        run.error = "; ".join(errors)[:MAX_ERROR_LENGTH] or None
        run.status = STATUS_SUCCESS if not errors else STATUS_PARTIAL if saved else STATUS_FAILED
        session.add(run)
        await session.commit()
        logger.info("news sync finished", extra={"status": run.status, "items": saved})
    await invalidate_all()
    return run


async def create_manual_article(session: AsyncSession, dto: NewsDTO) -> int:
    sports = await _sport_ids(session)
    article_id = await save_article(
        session, dto, sports.get(dto.sport_slug or ""), _Tagger(session)
    )
    await session.commit()
    await invalidate_all()
    return article_id


# ---- read side -------------------------------------------------------------------------------

TRANSFER_FILTER = "transfer"  # pseudo category: official + rumour
TRANSFER_CATEGORIES = ("transfer_official", "transfer_rumour")
ARCHIVE_SCAN_LIMIT = 20000


@dataclass(frozen=True)
class NewsFilters:
    category: str | None = None
    sport: str | None = None
    team: int | None = None
    player: int | None = None
    competition: int | None = None
    breaking: bool | None = None
    month: str | None = None  # YYYY-MM
    q: str | None = None
    language: str | None = None
    max_age_hours: int | None = None  # e.g. breaking news from the last 48 hours


def month_bounds(month: str) -> tuple[datetime, datetime]:
    """'2026-10' -> [2026-10-01, 2026-11-01) in UTC; ValueError on bad input."""
    start = datetime.strptime(month, "%Y-%m").replace(tzinfo=UTC)
    end = (
        start.replace(year=start.year + 1, month=1)
        if start.month == 12
        else start.replace(month=start.month + 1)
    )
    return start, end


def _filtered(filters: NewsFilters, *, with_month: bool = True):
    stmt = select(NewsArticle)
    if filters.category == TRANSFER_FILTER:
        stmt = stmt.where(NewsArticle.category.in_(TRANSFER_CATEGORIES))
    elif filters.category:
        stmt = stmt.where(NewsArticle.category == filters.category)
    if filters.sport:
        stmt = stmt.where(
            NewsArticle.sport_id.in_(select(Sport.id).where(Sport.slug == filters.sport))
        )
    for column, value in (
        (NewsTag.team_id, filters.team),
        (NewsTag.player_id, filters.player),
        (NewsTag.competition_id, filters.competition),
    ):
        if value is not None:
            stmt = stmt.where(NewsArticle.id.in_(select(NewsTag.article_id).where(column == value)))
    if filters.breaking is not None:
        stmt = stmt.where(NewsArticle.is_breaking == filters.breaking)
    if filters.language:
        stmt = stmt.where(NewsArticle.language == filters.language)
    if filters.q:
        like = f"%{filters.q.replace('%', '').replace('_', '')}%"
        stmt = stmt.where(NewsArticle.title.ilike(like) | NewsArticle.summary.ilike(like))
    if filters.max_age_hours:
        since = datetime.now(UTC) - timedelta(hours=filters.max_age_hours)
        stmt = stmt.where(NewsArticle.published_at >= since)
    if with_month and filters.month:
        start, end = month_bounds(filters.month)
        stmt = stmt.where(NewsArticle.published_at >= start, NewsArticle.published_at < end)
    return stmt


def _with_tags(stmt):
    return stmt.options(
        selectinload(NewsArticle.sport),
        selectinload(NewsArticle.tags).options(
            joinedload(NewsTag.team).joinedload(Team.sport),
            joinedload(NewsTag.player).joinedload(Player.sport),
            joinedload(NewsTag.competition).joinedload(Competition.sport),
        ),
    )


def _tag_out(tag: NewsTag) -> NewsTagOut | None:
    if tag.team:
        return NewsTagOut(kind="team", id=tag.team.id, name=tag.team.name,
                          sport_slug=tag.team.sport.slug)  # fmt: skip
    if tag.player:
        return NewsTagOut(kind="player", id=tag.player.id, name=tag.player.name,
                          sport_slug=tag.player.sport.slug)  # fmt: skip
    if tag.competition:
        c = tag.competition
        return NewsTagOut(kind="competition", id=c.id, name=c.name, sport_slug=c.sport.slug,
                          slug=c.slug)  # fmt: skip
    return None


def news_out(article: NewsArticle) -> NewsOut:
    return NewsOut(
        id=article.id,
        title=article.title,
        summary=article.summary,
        url=article.url,
        image_url=article.image_url,
        author=article.author,
        source=article.source.removeprefix(SOURCE_PREFIX),
        published_at=article.published_at,
        category=article.category,  # type: ignore[arg-type]
        is_breaking=article.is_breaking,
        language=article.language,
        sport_slug=article.sport.slug if article.sport else None,
        tags=[t for tag in article.tags if (t := _tag_out(tag))],
    )


async def list_news(
    session: AsyncSession, filters: NewsFilters, page: int, page_size: int
) -> NewsList:
    async def load() -> NewsList:
        base = _filtered(filters)
        total = await session.scalar(select(func.count()).select_from(base.subquery())) or 0
        stmt = _with_tags(base).order_by(NewsArticle.published_at.desc(), NewsArticle.id.desc())
        rows = (await session.scalars(stmt.offset((page - 1) * page_size).limit(page_size))).all()
        return NewsList(
            items=[news_out(a) for a in rows], total=total, page=page, page_size=page_size
        )

    return await cached(f"news:{filters}:{page}:{page_size}", NewsList, load)


async def get_article(session: AsyncSession, article_id: int) -> NewsOut:
    article = (
        await session.scalars(_with_tags(select(NewsArticle).where(NewsArticle.id == article_id)))
    ).first()
    if article is None:
        raise NotFoundError("Haber")
    return news_out(article)


async def news_archive(session: AsyncSession, filters: NewsFilters) -> NewsArchive:
    """Article counts per month (newest first), honouring every filter except the month."""

    async def load() -> NewsArchive:
        stmt = (
            _filtered(filters, with_month=False)
            .with_only_columns(NewsArticle.published_at)
            .order_by(NewsArticle.published_at.desc())
            .limit(ARCHIVE_SCAN_LIMIT)
        )
        counts: dict[str, int] = defaultdict(int)
        for published in (await session.scalars(stmt)).all():
            counts[published.astimezone(UTC).strftime("%Y-%m")] += 1
        return NewsArchive(months=[ArchiveMonth(month=m, count=c) for m, c in counts.items()])

    return await cached(f"news-archive:{filters}", NewsArchive, load)
