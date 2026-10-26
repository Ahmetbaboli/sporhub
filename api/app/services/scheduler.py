import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.adapters.registry import adapter_names, create_adapter
from app.core.config import Settings
from app.db.session import get_sessionmaker
from app.services.sync_service import run_sync

logger = logging.getLogger(__name__)


async def sync_job(name: str, settings: Settings) -> None:
    adapter = create_adapter(name, settings)
    try:
        await run_sync(get_sessionmaker(), adapter)
    except Exception:
        logger.exception("scheduled sync crashed", extra={"adapter": name})
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
    return scheduler
