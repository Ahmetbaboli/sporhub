"""Removing demo (fixture / sample-news) rows from a database.

Demo rows are recognised only by their `demo:` source prefix (see app.core.data_mode), so real
data is never touched. Child rows are deleted explicitly in FK order: SQLite does not enforce
ON DELETE CASCADE unless asked to, and PostgreSQL would reject the parent deletes otherwise.
"""

import logging

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import invalidate_all
from app.core.data_mode import DEMO_PREFIX
from app.models import (
    Competition,
    Event,
    EventParticipant,
    Favorite,
    NewsArticle,
    NewsTag,
    Player,
    PlayerStat,
    Season,
    Standing,
    Team,
)

logger = logging.getLogger(__name__)

DEMO_LIKE = f"{DEMO_PREFIX}%"


async def purge_demo(session: AsyncSession) -> dict[str, int]:
    """Delete every demo row; returns the number of deleted rows per table."""
    demo_comps = select(Competition.id).where(Competition.source.like(DEMO_LIKE))
    demo_seasons = select(Season.id).where(Season.competition_id.in_(demo_comps))
    demo_events = select(Event.id).where(
        or_(Event.source.like(DEMO_LIKE), Event.season_id.in_(demo_seasons))
    )
    demo_teams = select(Team.id).where(Team.source.like(DEMO_LIKE))
    demo_players = select(Player.id).where(Player.source.like(DEMO_LIKE))
    demo_news = select(NewsArticle.id).where(NewsArticle.source.like(DEMO_LIKE))

    steps = [
        (
            "news_tags",
            delete(NewsTag).where(
                or_(
                    NewsTag.article_id.in_(demo_news),
                    NewsTag.team_id.in_(demo_teams),
                    NewsTag.player_id.in_(demo_players),
                    NewsTag.competition_id.in_(demo_comps),
                )
            ),
        ),
        ("news_articles", delete(NewsArticle).where(NewsArticle.source.like(DEMO_LIKE))),
        (
            "favorites",
            delete(Favorite).where(
                or_(
                    Favorite.team_id.in_(demo_teams),
                    Favorite.player_id.in_(demo_players),
                    Favorite.competition_id.in_(demo_comps),
                )
            ),
        ),
        (
            "player_stats",
            delete(PlayerStat).where(
                or_(PlayerStat.season_id.in_(demo_seasons), PlayerStat.player_id.in_(demo_players))
            ),
        ),
        (
            "standings",
            delete(Standing).where(
                or_(
                    Standing.season_id.in_(demo_seasons),
                    Standing.team_id.in_(demo_teams),
                    Standing.player_id.in_(demo_players),
                )
            ),
        ),
        (
            "event_participants",
            delete(EventParticipant).where(
                or_(
                    EventParticipant.event_id.in_(demo_events),
                    EventParticipant.team_id.in_(demo_teams),
                    EventParticipant.player_id.in_(demo_players),
                )
            ),
        ),
        ("events", delete(Event).where(Event.id.in_(demo_events))),
        ("seasons", delete(Season).where(Season.id.in_(demo_seasons))),
        ("competitions", delete(Competition).where(Competition.source.like(DEMO_LIKE))),
        ("players", delete(Player).where(Player.source.like(DEMO_LIKE))),
        ("teams", delete(Team).where(Team.source.like(DEMO_LIKE))),
    ]
    counts: dict[str, int] = {}
    for table, statement in steps:
        result = await session.execute(statement)
        counts[table] = result.rowcount or 0  # type: ignore[attr-defined]
    await session.commit()
    await invalidate_all()
    if any(counts.values()):
        logger.info("demo data purged", extra={"deleted": counts})
    return counts


async def has_demo_rows(session: AsyncSession) -> bool:
    for model in (Competition, Team, Player, Event, NewsArticle):
        found = await session.scalar(
            select(model.id).where(model.source.like(DEMO_LIKE)).limit(1)  # type: ignore[attr-defined]
        )
        if found is not None:
            return True
    return False
