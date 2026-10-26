"""Small cache layer: Redis when REDIS_URL is set, in-process memory otherwise."""

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Protocol, TypeVar

import redis.asyncio as redis
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)
KEY_PREFIX = "js:"
T = TypeVar("T", bound=BaseModel)


class CacheBackend(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def set(self, key: str, value: str, ttl: int) -> None: ...
    async def clear(self) -> None: ...


class MemoryCache:
    def __init__(self) -> None:
        self._data: dict[str, tuple[float, str]] = {}

    async def get(self, key: str) -> str | None:
        entry = self._data.get(key)
        if entry is None or entry[0] < time.monotonic():
            self._data.pop(key, None)
            return None
        return entry[1]

    async def set(self, key: str, value: str, ttl: int) -> None:
        self._data[key] = (time.monotonic() + ttl, value)

    async def clear(self) -> None:
        self._data.clear()


class RedisCache:
    def __init__(self, url: str) -> None:
        self._client = redis.from_url(url, decode_responses=True)

    async def get(self, key: str) -> str | None:
        return await self._client.get(KEY_PREFIX + key)

    async def set(self, key: str, value: str, ttl: int) -> None:
        await self._client.set(KEY_PREFIX + key, value, ex=ttl)

    async def clear(self) -> None:
        async for key in self._client.scan_iter(match=f"{KEY_PREFIX}*"):
            await self._client.delete(key)


_backend: CacheBackend | None = None


def get_cache() -> CacheBackend:
    global _backend
    if _backend is None:
        url = get_settings().redis_url
        _backend = RedisCache(url) if url else MemoryCache()
    return _backend


def reset_cache() -> None:
    global _backend
    _backend = None


async def cached(
    key: str, model: type[T], loader: Callable[[], Awaitable[T]], ttl: int | None = None
) -> T:
    """Return the cached model for `key`, computing and storing it on a miss.

    Cache failures never break a request: they are logged and the loader result is returned.
    """
    cache = get_cache()
    try:
        hit = await cache.get(key)
        if hit is not None:
            return model.model_validate_json(hit)
    except Exception as exc:
        logger.warning("cache read failed", extra={"key": key, "error": str(exc)})
    value = await loader()
    try:
        await cache.set(key, value.model_dump_json(), ttl or get_settings().cache_ttl_seconds)
    except Exception as exc:
        logger.warning("cache write failed", extra={"key": key, "error": str(exc)})
    return value


async def invalidate_all() -> None:
    try:
        await get_cache().clear()
    except Exception as exc:
        logger.warning("cache clear failed", extra={"error": str(exc)})
