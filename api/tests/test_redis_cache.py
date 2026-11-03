"""RedisCache against fakeredis always, and against a real Redis when TEST_REDIS_URL is set."""

import os

import fakeredis
import pytest

from app.core import cache
from app.core.cache import RedisCache, cached
from app.core.config import get_settings
from app.schemas.api import HealthOut
from app.services.health import _redis

REDIS_URL = os.environ.get("TEST_REDIS_URL", "")


def _fake_cache() -> RedisCache:
    backend = RedisCache("redis://localhost:6379/15")
    backend._client = fakeredis.FakeAsyncRedis(decode_responses=True)
    return backend


def _real_cache() -> RedisCache:
    return RedisCache(REDIS_URL)


@pytest.fixture(
    params=[
        pytest.param(_fake_cache, id="fakeredis"),
        pytest.param(
            _real_cache,
            id="redis",
            marks=pytest.mark.skipif(not REDIS_URL, reason="needs TEST_REDIS_URL"),
        ),
    ]
)
async def backend(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch):
    instance: RedisCache = request.param()
    await instance.clear()
    monkeypatch.setattr(cache, "_backend", instance)
    yield instance
    await instance.clear()


async def test_set_get_and_prefix(backend: RedisCache) -> None:
    await backend.set("k", "v", 30)
    assert await backend.get("k") == "v"
    assert await backend._client.get("js:k") == "v"
    assert await backend.get("missing") is None


async def test_entries_expire(backend: RedisCache) -> None:
    await backend.set("short", "v", 1)
    assert await backend._client.ttl("js:short") in (0, 1)


async def test_clear_only_removes_our_keys(backend: RedisCache) -> None:
    await backend._client.set("other:key", "keep")
    await backend.set("a", "1", 30)
    await backend.clear()
    assert await backend.get("a") is None
    assert await backend._client.get("other:key") == "keep"
    await backend._client.delete("other:key")


async def test_cached_wrapper_uses_redis(backend: RedisCache) -> None:
    calls = 0

    async def loader() -> HealthOut:
        nonlocal calls
        calls += 1
        return HealthOut(status="ok", version="9")

    first = await cached("health", HealthOut, loader, ttl=30)
    second = await cached("health", HealthOut, loader, ttl=30)
    assert first == second and calls == 1


class _BrokenClient:
    def __init__(self) -> None:
        self.calls = 0

    async def get(self, key: str) -> str | None:
        self.calls += 1
        raise ConnectionError("refused")

    async def set(self, key: str, value: str, ex: int) -> None:
        self.calls += 1
        raise ConnectionError("refused")

    async def ping(self) -> bool:
        self.calls += 1
        raise ConnectionError("refused")


async def test_unreachable_redis_is_skipped_during_cooldown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = RedisCache("redis://localhost:6379/15")
    client = _BrokenClient()
    backend._client = client
    monkeypatch.setattr(cache, "_backend", backend)

    async def loader() -> HealthOut:
        return HealthOut(status="ok", version="9")

    for _ in range(3):
        assert (await cached("health", HealthOut, loader)).version == "9"
    assert client.calls == 1

    backend._down_until = 0.0
    with pytest.raises(ConnectionError):
        await backend.get("health")
    assert client.calls == 2


async def test_health_reports_redis_down_during_cooldown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = RedisCache("redis://localhost:6379/15")
    backend._client = _BrokenClient()
    backend._down_until = float("inf")
    monkeypatch.setattr(cache, "_backend", backend)
    settings = get_settings().model_copy(update={"redis_url": "redis://localhost:6379/15"})

    check = await _redis(settings)
    assert check is not None and check.ok is False
