"""Delete every demo (fixture / sample-news) row:  python -m app.scripts.purge_demo

Safe on a real database: only rows whose source starts with "demo:" are removed.
"""

import asyncio
import json

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import get_engine, get_sessionmaker
from app.services.demo_data import purge_demo


async def run() -> dict[str, int]:
    async with get_sessionmaker()() as session:
        counts = await purge_demo(session)
    await get_engine().dispose()
    return counts


def main() -> None:
    configure_logging(get_settings().log_level)
    print(json.dumps(asyncio.run(run()), indent=2))


if __name__ == "__main__":
    main()
