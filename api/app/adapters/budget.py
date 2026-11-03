"""Central request budget per provider (sliding windows over the verified limits).

Limits come from docs/DATA-SOURCES.md and are applied with HEADROOM so a restart (counters live in
memory) or clock skew never pushes us over the provider's real limit. Short windows (second,
minute) make callers wait; long windows (hour, day) refuse the request instead of stalling a
sync for an hour. A 429's Retry-After pauses the whole provider.
"""

import asyncio
import math
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

HEADROOM = 0.9
SECOND, MINUTE, HOUR, DAY = 1, 60, 3600, 86400
# Waiting longer than this for a window is pointless inside a sync: refuse instead.
MAX_WAIT_SECONDS = 70.0


@dataclass(frozen=True)
class Limits:
    per_second: int | None = None
    per_minute: int | None = None
    per_hour: int | None = None
    per_day: int | None = None

    def windows(self) -> list[tuple[str, int, int]]:
        raw = [
            ("second", SECOND, self.per_second),
            ("minute", MINUTE, self.per_minute),
            ("hour", HOUR, self.per_hour),
            ("day", DAY, self.per_day),
        ]
        return [(name, span, max(1, math.floor(n * HEADROOM))) for name, span, n in raw if n]


# Verified 2026-11-02 (docs/DATA-SOURCES.md).
PROVIDER_LIMITS: dict[str, Limits] = {
    "football-data": Limits(per_minute=10),
    "thesportsdb": Limits(per_minute=100),
    "balldontlie": Limits(per_minute=5),
    "jolpica": Limits(per_second=4, per_hour=500),
    # ESPN documents no limits for its site API: stay far below anything a browser would do.
    "espn": Limits(per_minute=20, per_hour=200),
}


class BudgetExhaustedError(RuntimeError):
    def __init__(self, source: str, window: str, retry_in: float) -> None:
        super().__init__(f"{source}: {window} request budget used up; retry in {retry_in:.0f}s")
        self.retry_in = retry_in


class RequestBudget:
    def __init__(
        self,
        source: str,
        limits: Limits,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], object] = asyncio.sleep,
    ) -> None:
        self.source = source
        self._windows = limits.windows()
        self._calls: deque[float] = deque()
        self._paused_until = 0.0
        self._clock = clock
        self._sleep = sleep
        self._lock = asyncio.Lock()

    def _used(self, span: int, now: float) -> int:
        return sum(1 for t in self._calls if t > now - span)

    def _wait_needed(self, now: float) -> tuple[float, str]:
        """Seconds until a call is allowed, and which window decides it."""
        wait, reason = max(0.0, self._paused_until - now), "retry-after"
        for name, span, limit in self._windows:
            inside = [t for t in self._calls if t > now - span]
            if len(inside) >= limit:
                free_at = inside[len(inside) - limit] + span
                if free_at - now > wait:
                    wait, reason = free_at - now, name
        return wait, reason

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = self._clock()
                longest = max((span for _, span, _ in self._windows), default=0)
                while self._calls and self._calls[0] <= now - longest:
                    self._calls.popleft()
                wait, reason = self._wait_needed(now)
                if wait <= 0:
                    self._calls.append(now)
                    return
                if wait > MAX_WAIT_SECONDS:
                    raise BudgetExhaustedError(self.source, reason, wait)
                await self._sleep(wait)  # type: ignore[misc]

    def pause(self, seconds: float) -> None:
        """Honour a provider's Retry-After for every caller of this provider."""
        self._paused_until = max(self._paused_until, self._clock() + seconds)

    def snapshot(self) -> dict[str, dict[str, int]]:
        now = self._clock()
        return {
            name: {
                "limit": limit,
                "used": self._used(span, now),
                "remaining": limit - self._used(span, now),
            }
            for name, span, limit in self._windows
        }


_BUDGETS: dict[str, RequestBudget] = {}


def get_budget(source: str) -> RequestBudget | None:
    """Process-wide budget for a provider (None when the provider has no documented limit)."""
    limits = PROVIDER_LIMITS.get(source)
    if limits is None:
        return None
    if source not in _BUDGETS:
        _BUDGETS[source] = RequestBudget(source, limits)
    return _BUDGETS[source]


def all_budgets() -> dict[str, dict[str, dict[str, int]]]:
    return {name: get_budget(name).snapshot() for name in PROVIDER_LIMITS}  # type: ignore[union-attr]


def reset_budgets() -> None:
    """Tests only."""
    _BUDGETS.clear()
