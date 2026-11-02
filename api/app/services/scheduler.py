"""Background refresh. One tick per minute asks the planner what is due (services/sync_planner).

Runs only in DATA_MODE=live and only in the process that holds the scheduler lock
(core/locks.py), so several API instances never sync twice.
"""

import logging
from collections import defaultdict
from datetime import timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import delete

from app.adapters.news_rss import RssNewsAdapter
from app.adapters.registry import adapter_names, create_adapter
from app.core.config import Settings
from app.db.session import get_sessionmaker
from app.models import SyncRun
from app.services.news_service import run_news_sync
from app.services.sync_planner import SyncPlanner, competition_tiers, utcnow
from app.services.sync_service import run_sync

logger = logging.getLogger(__name__)

TICK_SECONDS = 60
SYNC_RUN_RETENTION = timedelta(days=30)
PLANNER = SyncPlanner()


async def sync_job(name: str, settings: Settings) -> None:
    """Full sync of one adapter (manual/admin use); skips unconfigured and demo adapters."""
    adapter = create_adapter(name, settings)
    if not adapter.configured or adapter.use_fixtures:
        logger.info("scheduled sync skipped", extra={"adapter": name})
        await adapter.aclose()
        return
    try:
        await run_sync(get_sessionmaker(), adapter)
    except Exception:
        logger.exception("scheduled sync crashed", extra={"adapter": name})
    finally:
        await adapter.aclose()


async def refresh_adapter(name: str, settings: Settings, planner: SyncPlanner) -> int:
    """Run whatever the planner says is due for one adapter; returns the number of syncs run."""
    adapter = create_adapter(name, settings)
    try:
        if not adapter.configured or adapter.use_fixtures:
            return 0
        now = utcnow()
        maker = get_sessionmaker()
        async with maker() as session:
            tiers = await competition_tiers(session, adapter, now)
        due = planner.due(name, list(adapter.default_competitions), tiers, now)
        groups: dict[frozenset[str], list[str]] = defaultdict(list)
        for comp, parts in due:
            groups[parts].append(comp)
        for parts, comps in groups.items():
            run = await run_sync(maker, adapter, tuple(comps), parts)
            logger.info(
                "planned sync",
                extra={
                    "adapter": name,
                    "competitions": comps,
                    "parts": sorted(parts),
                    "status": run.status,
                },  # fmt: skip
            )
            # Marked even on failure: the next attempt waits one interval instead of hammering.
            for comp in comps:
                planner.mark(name, comp, parts, now)
        return len(groups)
    except Exception:
        logger.exception("planned sync crashed", extra={"adapter": name})
        return 0
    finally:
        await adapter.aclose()


async def tick(settings: Settings, planner: SyncPlanner = PLANNER) -> None:
    for name in adapter_names():
        await refresh_adapter(name, settings, planner)


async def news_job(settings: Settings) -> None:
    adapter = RssNewsAdapter(settings)
    try:
        await run_news_sync(get_sessionmaker(), adapter)
    except Exception:
        logger.exception("scheduled news sync crashed")
    finally:
        await adapter.aclose()


async def prune_sync_runs() -> None:
    async with get_sessionmaker()() as session:
        await session.execute(
            delete(SyncRun).where(SyncRun.started_at < utcnow() - SYNC_RUN_RETENTION)
        )
        await session.commit()


def build_scheduler(settings: Settings) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    if settings.data_mode != "live":
        return scheduler  # demo data is loaded once by the seed command, never refreshed
    common = {"max_instances": 1, "coalesce": True}
    scheduler.add_job(tick, "interval", seconds=TICK_SECONDS, args=[settings], id="tick", **common)
    if settings.news_feeds:
        scheduler.add_job(
            news_job,
            "interval",
            minutes=settings.news_interval_minutes,
            args=[settings],
            id="sync:news",
            **common,
        )
    scheduler.add_job(prune_sync_runs, "interval", hours=1, id="prune", **common)
    return scheduler
