"""RedisCache against fakeredis always, and against a real Redis when TEST_REDIS_URL is set."""

import os

import fakeredis
import pytest

from app.core import cache
from app.core.cache import RedisCache, cached
from app.schemas.api import HealthOut

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
