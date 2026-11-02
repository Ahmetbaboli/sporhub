"""Decides what to refresh, and how often, from what is happening right now.

Tiers per competition (computed from stored events):
  * live    — a match is live, or kicks off within the next 15 minutes / started < 3 h ago
  * today   — something is scheduled today (UTC +/- 12 h)
  * weekend — F1: a race within 3 days (practice/qualifying happen in that window)
  * idle    — everything else
Live/today/weekend refresh only scores and tables; teams, rosters and scorers once a day.
Intervals respect each provider's request budget (adapters/budget.py) — the budget is still
the hard guarantee, these intervals just avoid hitting it.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import BaseAdapter
from app.models import Competition, Event, Season
from app.services.sync_service import ALL_PARTS, SCORE_PARTS

LIVE_LOOKAHEAD = timedelta(minutes=15)
LIVE_LOOKBACK = timedelta(hours=3)
TODAY_WINDOW = timedelta(hours=12)
RACE_WEEKEND_WINDOW = timedelta(days=3)
ROSTER_INTERVAL = timedelta(hours=24)

DEFAULT_INTERVALS = {
    "live": timedelta(minutes=2),
    "today": timedelta(minutes=15),
    "weekend": timedelta(minutes=30),
    "idle": timedelta(hours=6),
}
# balldontlie free tier is 5 requests/minute and one games sync pages through several requests.
ADAPTER_INTERVALS: dict[str, dict[str, timedelta]] = {
    "balldontlie": {
        **DEFAULT_INTERVALS,
        "live": timedelta(minutes=10),
        "today": timedelta(minutes=30),
    },
    "jolpica": {**DEFAULT_INTERVALS, "idle": timedelta(hours=12)},
}


def tier_for(events: list[tuple[str, datetime, str]], now: datetime, is_race: bool) -> str:
    """events: (status, start_time, kind) of one competition's current season."""
    for status, start, _ in events:
        if status == "live" or (
            status == "scheduled" and now - LIVE_LOOKBACK <= start <= now + LIVE_LOOKAHEAD
        ):
            return "live"
    if is_race and any(abs(start - now) <= RACE_WEEKEND_WINDOW for _, start, _ in events):
        return "weekend"
    if any(abs(start - now) <= TODAY_WINDOW for _, start, _ in events):
        return "today"
    return "idle"


async def competition_tiers(
    session: AsyncSession, adapter: BaseAdapter, now: datetime
) -> dict[str, str]:
    """external competition id -> tier, for competitions this adapter has already stored."""
    rows = await session.execute(
        select(Competition.external_id, Event.status, Event.start_time, Event.kind)
        .join(Season, Season.competition_id == Competition.id)
        .join(Event, Event.season_id == Season.id)
        .where(
            Competition.source == adapter.record_source,
            Season.is_current,
            Event.start_time >= now - timedelta(days=4),
            Event.start_time <= now + timedelta(days=4),
        )
    )
    by_comp: dict[str, list[tuple[str, datetime, str]]] = {}
    for ext, status, start, kind in rows:
        by_comp.setdefault(ext, []).append((status, start, kind))
    stored = await session.scalars(
        select(Competition.external_id).where(Competition.source == adapter.record_source)
    )
    return {
        ext: tier_for(by_comp.get(ext, []), now, adapter.sport_slug == "formula-1")
        for ext in stored
    }


@dataclass
class SyncPlanner:
    """In-memory schedule state. Exactly one scheduler process runs (see core/locks.py)."""

    last_scores: dict[tuple[str, str], datetime] = field(default_factory=dict)
    last_full: dict[tuple[str, str], datetime] = field(default_factory=dict)

    def due(
        self, adapter: str, competitions: list[str], tiers: dict[str, str], now: datetime
    ) -> list[tuple[str, frozenset[str]]]:
        intervals = ADAPTER_INTERVALS.get(adapter, DEFAULT_INTERVALS)
        plan = []
        for comp in competitions:
            key = (adapter, comp)
            full_at = self.last_full.get(key)
            if comp not in tiers or full_at is None or now - full_at >= ROSTER_INTERVAL:
                plan.append((comp, ALL_PARTS))  # first time ever, or the daily full refresh
                continue
            interval = intervals[tiers[comp]]
            last = max(self.last_scores.get(key, full_at), full_at)
            if now - last >= interval:
                plan.append((comp, SCORE_PARTS))
        return plan

    def mark(self, adapter: str, comp: str, parts: frozenset[str], now: datetime) -> None:
        self.last_scores[(adapter, comp)] = now
        if parts == ALL_PARTS:
            self.last_full[(adapter, comp)] = now


def utcnow() -> datetime:
    return datetime.now(UTC)
