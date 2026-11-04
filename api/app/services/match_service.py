"""Match details (lineups, key moments, team stats), fetched from the source on demand.

Only opened match pages cost a request: details are not part of the scheduled sync (a
season is ~300 matches), they are fetched when asked and cached by match state.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import BaseAdapter
from app.adapters.budget import BudgetExhaustedError
from app.adapters.http_fixture import SourceNotConfiguredError
from app.adapters.registry import ADAPTERS, create_adapter
from app.core.cache import cached
from app.core.config import Settings
from app.core.data_mode import display_source
from app.core.errors import NotFoundError
from app.models.events import Event
from app.repositories import queries
from app.schemas.match import MatchDetailsOut, UnavailableReason

logger = logging.getLogger(__name__)

# A page must never hang on the provider: past this, show "temporarily unavailable".
FETCH_TIMEOUT_SECONDS = 8.0
# Lineups appear roughly an hour before kick-off; earlier requests would only come back empty.
PRE_MATCH_WINDOW = timedelta(hours=3)
TTL_LIVE_SECONDS = 60
TTL_UPCOMING_SECONDS = 30 * 60
TTL_FINISHED_SECONDS = 6 * 3600
NO_DETAILS_STATUSES = ("postponed", "cancelled")
FETCH_ERRORS = (
    TimeoutError,
    BudgetExhaustedError,
    SourceNotConfiguredError,
    httpx.HTTPError,
)


def supports_details(source: str) -> bool:
    factory = ADAPTERS.get(source)
    method = getattr(factory, "fetch_match_details", None)
    return method is not None and method is not BaseAdapter.fetch_match_details


def _ttl(status: str) -> int:
    if status == "live":
        return TTL_LIVE_SECONDS
    return TTL_FINISHED_SECONDS if status == "finished" else TTL_UPCOMING_SECONDS


def _empty(event: Event, reason: UnavailableReason, source: str | None) -> MatchDetailsOut:
    return MatchDetailsOut(event_id=event.id, available=False, reason=reason, source=source)


def _too_early(event: Event, now: datetime) -> bool:
    return event.status == "scheduled" and event.start_time - now > PRE_MATCH_WINDOW


async def _fetch(event: Event, source: str, settings: Settings) -> MatchDetailsOut:
    adapter = create_adapter(source, settings)
    try:
        details = await asyncio.wait_for(
            adapter.fetch_match_details(event.season.competition.external_id, event.external_id),
            FETCH_TIMEOUT_SECONDS,
        )
    finally:
        await adapter.aclose()
    if details is None or details.is_empty():
        reason: UnavailableReason = "not_started" if event.status == "scheduled" else "unavailable"
        return _empty(event, reason, source)
    return MatchDetailsOut(
        event_id=event.id,
        available=True,
        source=source,
        **details.model_dump(),
        fetched_at=datetime.now(UTC),
    )


async def get_match_details(
    session: AsyncSession, event_id: int, settings: Settings
) -> MatchDetailsOut:
    event = await queries.get_event(session, event_id)
    if event is None:
        raise NotFoundError("Etkinlik")
    source = display_source(event.source)
    if not supports_details(source):
        return _empty(event, "unsupported", None)
    if event.status in NO_DETAILS_STATUSES or _too_early(event, datetime.now(UTC)):
        return _empty(event, "not_started", source)
    try:
        return await cached(
            f"match:{event_id}",
            MatchDetailsOut,
            lambda: _fetch(event, source, settings),
            _ttl(event.status),
        )
    except FETCH_ERRORS as exc:
        logger.warning(
            "match details unavailable",
            extra={"event_id": event_id, "source": source, "error": type(exc).__name__},
        )
        return _empty(event, "unavailable", source)
