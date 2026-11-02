"""/health: database, cache and data freshness in one cheap request."""

import time

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cache
from app.core.config import Settings
from app.models import SyncRun
from app.schemas.api import HealthCheck, HealthOut
from app.services.meta_service import SUCCESS_STATUSES, get_meta

HEALTH_PROBE_KEY = "health:probe"
MS = 1000


async def _database(session: AsyncSession) -> tuple[HealthCheck, bool]:
    started = time.perf_counter()
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        return HealthCheck(ok=False, detail=type(exc).__name__), False
    return HealthCheck(ok=True, ms=round((time.perf_counter() - started) * MS, 1)), True


async def _redis(settings: Settings) -> HealthCheck | None:
    if not settings.redis_url:
        return None  # in-memory cache: nothing to check
    started = time.perf_counter()
    try:
        await get_cache().get(HEALTH_PROBE_KEY)
    except Exception as exc:
        return HealthCheck(ok=False, detail=type(exc).__name__)
    return HealthCheck(ok=True, ms=round((time.perf_counter() - started) * MS, 1))


async def health_report(session: AsyncSession, settings: Settings) -> HealthOut:
    database, db_ok = await _database(session)
    redis = await _redis(settings)
    stale: list[str] = []
    last_sync = None
    if db_ok:
        meta = await get_meta(session, settings)
        stale = [s.name for s in meta.sources if s.configured and s.stale]
        last_sync = await session.scalar(
            select(func.max(SyncRun.finished_at)).where(SyncRun.status.in_(SUCCESS_STATUSES))
        )
    status = "down" if not db_ok else "degraded" if stale or (redis and not redis.ok) else "ok"
    return HealthOut(
        status=status,
        version=settings.app_version,
        data_mode=settings.data_mode,
        database=database,
        redis=redis,
        stale_sources=stale,
        last_sync_at=last_sync,
    )
