import time
from collections.abc import AsyncIterator
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.rate_limit import INTERNAL_KEY_HEADER, client_ip, request_weight

V1 = "/api/v1"
LIMIT = 5
INTERNAL_KEY = "web-server-key-for-tests"
MID_WINDOW = 1_800_000_030.0  # 30 s into a one-minute window


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """An outside visitor (the default test client looks like 127.0.0.1, which is exempt)."""
    transport = ASGITransport(app=app, client=("203.0.113.9", 50000))
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
def _limited(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    # The shared `settings` fixture is what every get_settings() returns during a test.
    settings.rate_limit_per_minute = LIMIT
    settings.internal_api_key = INTERNAL_KEY
    # Freeze the wall clock mid-window: a slow request (the forecast takes seconds on
    # PostgreSQL) must not let the next one start a fresh minute and slip past the limit.
    frozen = SimpleNamespace(time=lambda: MID_WINDOW, monotonic=time.monotonic)
    monkeypatch.setattr("app.core.rate_limit.time", frozen)


async def test_requests_over_the_quota_get_429_with_retry_after(client: AsyncClient) -> None:
    for i in range(LIMIT):
        r = await client.get(f"{V1}/sports")
        assert r.status_code == 200
        assert r.headers["X-RateLimit-Remaining"] == str(LIMIT - i - 1)
    r = await client.get(f"{V1}/sports")
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "rate_limited"
    assert 1 <= int(r.headers["Retry-After"]) <= 60


async def test_heavy_endpoints_cost_more(client: AsyncClient) -> None:
    r = await client.get(f"{V1}/competitions/premier-league/forecast")  # costs 5 = whole quota
    assert r.status_code == 200 and r.headers["X-RateLimit-Remaining"] == "0"
    assert (await client.get(f"{V1}/sports")).status_code == 429


async def test_web_server_with_the_internal_key_is_never_limited(client: AsyncClient) -> None:
    for _ in range(LIMIT * 3):
        r = await client.get(f"{V1}/sports", headers={INTERNAL_KEY_HEADER: INTERNAL_KEY})
        assert r.status_code == 200
    wrong = {INTERNAL_KEY_HEADER: "guess"}
    statuses = [(await client.get(f"{V1}/sports", headers=wrong)).status_code for _ in range(6)]
    assert statuses[-1] == 429


async def test_health_and_docs_are_exempt(client: AsyncClient) -> None:
    for _ in range(LIMIT + 2):
        assert (await client.get("/openapi.json")).status_code == 200
    assert (await client.get(f"{V1}/sports")).status_code == 200


async def test_limit_zero_turns_it_off(client: AsyncClient, settings: Settings) -> None:
    settings.rate_limit_per_minute = 0
    for _ in range(LIMIT * 2):
        assert (await client.get(f"{V1}/sports")).status_code == 200


def _request(forwarded: str | None, host: str = "10.0.0.1") -> object:
    headers = {"x-forwarded-for": forwarded} if forwarded else {}
    return SimpleNamespace(headers=headers, client=SimpleNamespace(host=host))


def test_client_ip_trusts_only_the_proxies_it_is_told_about() -> None:
    spoofed = _request("6.6.6.6, 203.0.113.7")  # client wrote 6.6.6.6, Render appended .7
    assert client_ip(spoofed, trusted_hops=1) == "203.0.113.7"  # type: ignore[arg-type]
    assert client_ip(spoofed, trusted_hops=0) == "10.0.0.1"  # type: ignore[arg-type]
    assert client_ip(_request(None), trusted_hops=1) == "10.0.0.1"  # type: ignore[arg-type]


def test_request_weight() -> None:
    assert request_weight("/api/v1/competitions/super-lig/forecast") == 5
    assert request_weight("/api/v1/events/4/details") == 3
    assert request_weight("/api/v1/teams/1") == 1


async def test_callers_on_this_machine_are_exempt(app: FastAPI) -> None:
    transport = ASGITransport(app=app, client=("127.0.0.1", 50000))
    async with AsyncClient(transport=transport, base_url="http://test") as local:
        for _ in range(LIMIT * 2):
            assert (await local.get(f"{V1}/sports")).status_code == 200
