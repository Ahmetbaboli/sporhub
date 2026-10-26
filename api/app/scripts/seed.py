"""Fill the database from bundled fixtures:  python -m app.scripts.seed"""

import asyncio
import logging

from app.adapters.registry import adapter_names, create_adapter
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import get_engine, get_sessionmaker
from app.services.sync_service import run_sync

logger = logging.getLogger(__name__)


async def seed() -> None:
    settings = get_settings().model_copy(update={"use_fixtures": True})
    maker = get_sessionmaker()
    for name in adapter_names():
        adapter = create_adapter(name, settings)
        try:
            run = await run_sync(maker, adapter)
            logger.info(
                "seeded", extra={"adapter": name, "status": run.status, "items": run.items_upserted}
            )
        finally:
            await adapter.aclose()
    await get_engine().dispose()


def main() -> None:
    configure_logging(get_settings().log_level)
    asyncio.run(seed())


if __name__ == "__main__":
    main()
