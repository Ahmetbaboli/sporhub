import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.adapters.news_rss import RssNewsAdapter
from app.adapters.registry import adapter_names, create_adapter
from app.core.config import Settings
from app.db.session import get_sessionmaker
from app.services.news_service import run_news_sync
from app.services.sync_service import run_sync

logger = logging.getLogger(__name__)


async def sync_job(name: str, settings: Settings) -> None:
    adapter = create_adapter(name, settings)
    if adapter.fell_back_to_fixtures:
        # Missing API key in a real deployment: never overwrite real data with sample data.
        logger.warning("scheduled sync skipped: API key missing", extra={"adapter": name})
        await adapter.aclose()
        return
    try:
        await run_sync(get_sessionmaker(), adapter)
    except Exception:
        logger.exception("scheduled sync crashed", extra={"adapter": name})
    finally:
        await adapter.aclose()


async def news_job(settings: Settings) -> None:
    adapter = RssNewsAdapter(settings)
    try:
        await run_news_sync(get_sessionmaker(), adapter)
    except Exception:
        logger.exception("scheduled news sync crashed")
    finally:
        await adapter.aclose()


def build_scheduler(settings: Settings) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    for name in adapter_names():
        scheduler.add_job(
            sync_job,
            "interval",
            minutes=settings.sync_interval_minutes,
            args=[name, settings],
            id=f"sync:{name}",
            max_instances=1,
            coalesce=True,
        )
    # Only real feeds are polled on a schedule; sample news is loaded by the seed command.
    if settings.news_feeds and not settings.use_fixtures:
        scheduler.add_job(
            news_job,
            "interval",
            minutes=settings.news_interval_minutes,
            args=[settings],
            id="sync:news",
            max_instances=1,
            coalesce=True,
        )
    return scheduler
