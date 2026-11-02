"""What the UI needs to be honest: data mode, which sports are configured, data freshness."""

from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.budget import all_budgets
from app.adapters.registry import ADAPTERS
from app.core.config import Settings
from app.core.redact import redact
from app.core.sources import SOURCES
from app.models import SyncRun
from app.schemas.meta import (
    AdminStatus,
    MetaOut,
    NewsFeedMeta,
    SourceMeta,
    SourceStatusDetail,
    SportMeta,
)
from app.services.sync_service import (
    STATUS_PARTIAL,
    STATUS_SKIPPED,
    STATUS_SUCCESS,
    ensure_sport,
)

SUCCESS_STATUSES = (STATUS_SUCCESS, STATUS_PARTIAL)
FAILED_STATUSES = ("failed", STATUS_PARTIAL)
# The slowest regular refresh is 12 h (F1 off-weekend); older data is shown as delayed.
STALE_AFTER = timedelta(hours=13)


def is_stale(
    configured: bool,
    last_success: datetime | None,
    last_attempt: datetime | None,
    last_status: str | None,
    now: datetime,
) -> bool:
    if not configured or last_attempt is None:
        return False  # nothing expected yet
    if last_success is None:
        return last_status in FAILED_STATUSES
    if last_success.tzinfo is None:
        last_success = last_success.replace(tzinfo=UTC)
    failed_since = last_status in FAILED_STATUSES
    return failed_since or now - last_success > STALE_AFTER


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


def _site(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


async def get_meta(session: AsyncSession, settings: Settings) -> MetaOut:
    runs = await _last_runs(session)
    now = datetime.now(UTC)
    sources = []
    for spec in SOURCES:
        success, attempt, status = runs.get(spec.name, (None, None, None))
        configured = spec.is_configured(settings)
        adapter = ADAPTERS.get(spec.name)
        sources.append(
            SourceMeta(
                name=spec.name,
                sport=spec.sport,
                configured=configured,
                last_success_at=success,
                last_attempt_at=attempt,
                last_status=status,
                stale=is_stale(configured, success, attempt, status, now),
                scores_delayed=bool(getattr(adapter, "scores_delayed", False)),
            )
        )
    sports = [
        SportMeta(
            slug=slug,
            name=name,
            configured=any(s.configured for s in sources if s.sport == slug),
            sources=[s.name for s in sources if s.sport == slug],
        )
        for slug, name in registered_sports().items()
    ]
    feeds = [] if settings.data_mode == "demo" else settings.news_feeds
    news_feeds = [
        NewsFeedMeta(
            name=str(f.get("name", "")),
            url=str(f.get("url", "")),
            site=_site(str(f.get("url", ""))),
            language=str(f.get("language", "tr")),
            sport=f.get("sport"),
        )
        for f in feeds
    ]
    return MetaOut(
        data_mode=settings.data_mode, sports=sports, sources=sources, news_feeds=news_feeds
    )


ERROR_PREVIEW_CHARS = 300
STATUS_WINDOW = timedelta(hours=24)


async def get_admin_status(session: AsyncSession, settings: Settings) -> AdminStatus:
    meta = await get_meta(session, settings)
    since = datetime.now(UTC) - STATUS_WINDOW
    budgets = all_budgets()
    details = []
    for source in meta.sources:
        runs = (
            await session.scalars(
                select(SyncRun)
                .where(SyncRun.adapter == source.name, SyncRun.started_at >= since)
                .order_by(SyncRun.started_at.desc())
            )
        ).all()
        counted = [r for r in runs if r.status != STATUS_SKIPPED]
        failures = [r for r in counted if r.status in FAILED_STATUSES]
        last_error = next((r.error for r in runs if r.error), None)
        details.append(
            SourceStatusDetail(
                **source.model_dump(),
                runs_24h=len(counted),
                failures_24h=len(failures),
                error_rate_24h=round(len(failures) / len(counted), 2) if counted else 0.0,
                last_error=redact(last_error, settings)[:ERROR_PREVIEW_CHARS]
                if last_error
                else None,
                budget=budgets.get(source.name, {}),
            )
        )
    return AdminStatus(
        data_mode=meta.data_mode, scheduler_enabled=settings.scheduler_enabled, sources=details
    )
