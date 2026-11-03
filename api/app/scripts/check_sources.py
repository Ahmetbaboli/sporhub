"""Report which data sources are configured and whether each answers one cheap request.

    python -m app.scripts.check_sources

Prints only "configured / not configured" and HTTP status codes. Key values are never read
into the output; the app loads its own environment (.env) as usual.
"""

import asyncio
import sys

import httpx

from app.core.config import get_settings
from app.core.sources import PROBE_TIMEOUT_SECONDS, SOURCES, probe_source
from app.core.tls import ssl_context


async def check() -> int:
    settings = get_settings()
    failures = 0
    async with httpx.AsyncClient(timeout=PROBE_TIMEOUT_SECONDS, verify=ssl_context()) as client:
        for spec in SOURCES:
            configured = spec.is_configured(settings)
            state = "yapılandırıldı" if configured else "YAPILANDIRILMADI"
            print(f"{spec.name:<14} {state:<17} {spec.description}")
            for result in await probe_source(spec, settings, client):
                mark = "ok " if result.ok else "HATA"
                print(f"    {mark} {result.target:<40} {result.detail}")
                failures += not result.ok
    return 1 if failures else 0


def main() -> None:
    # Windows consoles default to a legacy code page; Turkish labels need UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(asyncio.run(check()))


if __name__ == "__main__":
    main()
