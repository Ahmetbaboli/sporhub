"""What the UI needs to be honest: data mode, which sports are configured, data freshness."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.registry import ADAPTERS
from app.core.config import Settings
from app.core.sources import SOURCES
from app.models import SyncRun
from app.schemas.meta import MetaOut, SourceMeta, SportMeta
from app.services.sync_service import STATUS_PARTIAL, STATUS_SUCCESS, ensure_sport

SUCCESS_STATUSES = (STATUS_SUCCESS, STATUS_PARTIAL)


def registered_sports() -> dict[str, str]:
    """sport slug -> display name, from the adapter registry (stable, data-independent)."""
    return {factory.sport_slug: factory.sport_name for factory in ADAPTERS.values()}  # type: ignore[attr-defined]


async def ensure_registered_sports(session: AsyncSession) -> None:
    """Sports exist even before their first sync, so their pages can say "not configured"."""
    for slug, name in registered_sports().items():
        await ensure_sport(session, slug, name)
    await session.commit()


async def _last_runs(session: AsyncSession) -> dict[str, tuple]:
    success = dict(
        (
            await session.execute(
                select(SyncRun.adapter, func.max(SyncRun.finished_at))
                .where(SyncRun.status.in_(SUCCESS_STATUSES))
                .group_by(SyncRun.adapter)
            )
        ).all()
    )
    latest = dict(
        (
            await session.execute(
                select(SyncRun.adapter, func.max(SyncRun.started_at)).group_by(SyncRun.adapter)
            )
        ).all()
    )
    statuses = {}
    for adapter, started in latest.items():
        statuses[adapter] = await session.scalar(
            select(SyncRun.status).where(SyncRun.adapter == adapter, SyncRun.started_at == started)
        )
    return {a: (success.get(a), latest.get(a), statuses.get(a)) for a in latest}


async def get_meta(session: AsyncSession, settings: Settings) -> MetaOut:
    runs = await _last_runs(session)
    sources = [
        SourceMeta(
            name=spec.name,
            sport=spec.sport,
            configured=spec.is_configured(settings),
            last_success_at=runs.get(spec.name, (None, None, None))[0],
            last_attempt_at=runs.get(spec.name, (None, None, None))[1],
            last_status=runs.get(spec.name, (None, None, None))[2],
        )
        for spec in SOURCES
    ]
    sports = [
        SportMeta(
            slug=slug,
            name=name,
            configured=any(s.configured for s in sources if s.sport == slug),
            sources=[s.name for s in sources if s.sport == slug],
        )
        for slug, name in registered_sports().items()
    ]
    return MetaOut(data_mode=settings.data_mode, sports=sports, sources=sources)
