"""Re-run news tagging on stored articles:  python -m app.scripts.retag_news

Use after changing the tagging rules (app/services/news_service.py); idempotent.
"""

import asyncio
import json

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import get_engine, get_sessionmaker
from app.services.news_service import retag_all


async def run() -> dict[str, int]:
    async with get_sessionmaker()() as session:
        counts = await retag_all(session)
    await get_engine().dispose()
    return counts


def main() -> None:
    configure_logging(get_settings().log_level)
    print(json.dumps(asyncio.run(run()), indent=2))


if __name__ == "__main__":
    main()
