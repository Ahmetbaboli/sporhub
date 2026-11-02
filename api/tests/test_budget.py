import time

import httpx
import pytest
import respx

from app.adapters.budget import (
    HEADROOM,
    BudgetExhaustedError,
    Limits,
    RequestBudget,
    get_budget,
)
from app.adapters.http import RateLimitedClient, parse_retry_after


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0
        self.slept: list[float] = []

    def __call__(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


def budget(limits: Limits) -> tuple[RequestBudget, FakeClock]:
    clock = FakeClock()
    return RequestBudget("t", limits, clock=clock, sleep=clock.sleep), clock


async def test_minute_window_waits_and_is_never_exceeded() -> None:
    b, clock = budget(Limits(per_minute=10))
    allowed = int(10 * HEADROOM)
    calls = []
    for _ in range(allowed * 3):
        await b.acquire()
        calls.append(clock.now)
    # In every 60 s window there are at most `allowed` calls.
    for i, start in enumerate(calls):
        assert sum(1 for t in calls[i:] if t < start + 60) <= allowed
    assert clock.slept and max(clock.slept) <= 60


async def test_hour_window_refuses_instead_of_stalling() -> None:
    b, clock = budget(Limits(per_second=4, per_hour=10))
    for _ in range(int(10 * HEADROOM)):
        await b.acquire()
        clock.now += 1
    with pytest.raises(BudgetExhaustedError, match="hour"):
        await b.acquire()
    assert b.snapshot()["hour"]["remaining"] == 0


async def test_pause_blocks_everyone() -> None:
    b, clock = budget(Limits(per_minute=100))
    b.pause(30)
    await b.acquire()
    assert clock.slept == [30]


def test_parse_retry_after() -> None:
    assert parse_retry_after("12") == 12
    assert parse_retry_after(None) is None
    assert parse_retry_after("garbage") is None
    assert parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT") == 0  # in the past


@respx.mock
async def test_429_honours_retry_after_and_pauses_budget() -> None:
    route = respx.get("https://api.test/x").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "1"}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    b = RequestBudget("t", Limits(per_minute=100))
    client = RateLimitedClient("https://api.test", backoff_min=0.01, budget=b)
    started = time.monotonic()
    assert await client.get_json("/x") == {"ok": True}
    assert time.monotonic() - started >= 0.9  # waited the server's Retry-After, not backoff_min
    assert route.call_count == 2
    await client.aclose()


@respx.mock
async def test_exhausted_budget_makes_no_request() -> None:
    route = respx.get("https://api.test/x").mock(return_value=httpx.Response(200, json={}))
    b, clock = budget(Limits(per_hour=1))
    b._calls.append(clock.now)  # already used
    client = RateLimitedClient("https://api.test", budget=b)
    with pytest.raises(BudgetExhaustedError):
        await client.get_json("/x")
    assert route.call_count == 0
    await client.aclose()


def test_verified_limits_are_registered() -> None:
    assert get_budget("jolpica").snapshot()["hour"]["limit"] == int(500 * HEADROOM)  # type: ignore[union-attr]
    assert get_budget("football-data").snapshot()["minute"]["limit"] == 9  # type: ignore[union-attr]
    assert get_budget("unknown") is None
