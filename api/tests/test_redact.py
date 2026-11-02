import io
import logging

import httpx
import respx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.http import RateLimitedClient
from app.adapters.thesportsdb import BASE_URL, TheSportsDbAdapter
from app.core.config import Settings
from app.core.logging import JsonFormatter
from app.core.redact import redact
from app.models import SyncRun
from app.services.sync_service import run_sync

KEY = "premium-secret-key-42"


def test_redact_masks_long_secrets_only(settings: Settings) -> None:
    s = settings.model_copy(update={"thesportsdb_api_key": KEY, "balldontlie_api_key": "123"})
    assert redact(f"GET {BASE_URL}/{KEY}/x.php failed", s) == f"GET {BASE_URL}/***/x.php failed"
    assert redact("lookupleague.php?id=123", s) == "lookupleague.php?id=123"


@respx.mock
async def test_key_in_url_never_reaches_logs_or_sync_runs(
    maker: async_sessionmaker[AsyncSession], settings: Settings, monkeypatch
) -> None:
    live = settings.model_copy(update={"data_mode": "live", "thesportsdb_api_key": KEY})
    monkeypatch.setattr("app.core.redact.get_settings", lambda: live)
    respx.get(url__startswith=f"{BASE_URL}/{KEY}/").mock(return_value=httpx.Response(404))
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logging.getLogger().addHandler(handler)
    try:
        adapter = TheSportsDbAdapter(live)
        adapter._http = RateLimitedClient(BASE_URL, min_interval=0, backoff_min=0.01)
        run = await run_sync(maker, adapter)
        await adapter.aclose()
    finally:
        logging.getLogger().removeHandler(handler)
    assert run.status == "failed"
    async with maker() as s:
        stored = (await s.scalars(select(SyncRun.error))).all()
    assert stored and all(KEY not in (e or "") for e in stored)
    assert "***" in stored[0]
    assert KEY not in stream.getvalue()
