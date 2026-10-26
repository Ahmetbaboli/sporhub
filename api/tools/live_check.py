"""Smoke-test an adapter against the REAL API and print a summary (no DB, no secrets printed).

Run:  uv run python tools/live_check.py jolpica
Keys are read by Settings from the environment/.env; they are never printed.
"""

import asyncio
import sys
from collections import Counter

from app.adapters.registry import create_adapter
from app.core.config import Settings


async def main(name: str) -> None:
    settings = Settings(use_fixtures=False)
    adapter = create_adapter(name, settings)
    if adapter.use_fixtures:
        sys.exit(f"{name}: no API key configured; refusing to 'check' fixtures")
    try:
        comps = {c.external_id: c for c in await adapter.fetch_competitions()}
        for ext in adapter.default_competitions[:1]:
            comp = comps[ext]
            season = comp.season_key or ""
            print(
                f"competition {ext}: season {comp.season_label} {comp.season_start}..{comp.season_end}"
            )
            teams = await adapter.fetch_teams(ext, season)
            events = await adapter.fetch_events(ext, season)
            standings = await adapter.fetch_standings(ext, season)
            print(f"teams={len(teams)} players={sum(len(t.squad) for t in teams)}")
            print(f"events={len(events)} by status={dict(Counter(e.status for e in events))}")
            print(f"standings={len(standings)}")
            finished = [e for e in events if e.status == "finished"]
            if finished:
                last = finished[-1]
                print(
                    "last finished:",
                    last.name,
                    last.start_time.isoformat(),
                    [(p.position, p.extra.get("code"), p.points) for p in last.participants[:3]],
                )
    finally:
        await adapter.aclose()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
