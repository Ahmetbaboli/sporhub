"""Per-client request quota for the public API (fixed one-minute windows).

Every client IP gets RATE_LIMIT_PER_MINUTE "units" a minute; heavy endpoints cost more than
one. Over the quota the API answers 429 with Retry-After. Our own web server sends every page's
API calls from one address, so it is exempt when it presents INTERNAL_API_KEY. Callers on this
machine itself (127.0.0.1 / ::1: a local web server, scripts) are exempt as well.

Counters live in Redis when REDIS_URL is set (shared by all replicas), otherwise in this
process. A Redis failure falls back to the in-process counter rather than blocking traffic.
"""

import hmac
import logging
import math
import time
from collections.abc import Awaitable, Callable

import redis.asyncio as redis
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

WINDOW_SECONDS = 60
INTERNAL_KEY_HEADER = "X-Internal-Key"
KEY_PREFIX = "js:rl:"
REDIS_COOLDOWN_SECONDS = 30.0
EXEMPT_PATHS = frozenset({"/health", "/docs", "/redoc", "/openapi.json"})
LOOPBACK = frozenset({"127.0.0.1", "::1"})
# Cost of one request by path ending: these do real work (simulation, provider fetch, search).
WEIGHTS = (("/forecast", 5), ("/details", 3), ("/search", 2))
DEFAULT_WEIGHT = 1
# In-process counters are pruned once this many windows are held.
MAX_MEMORY_KEYS = 50_000


def request_weight(path: str) -> int:
    return next((w for suffix, w in WEIGHTS if path.endswith(suffix)), DEFAULT_WEIGHT)


def client_ip(request: Request, trusted_hops: int) -> str:
    """The caller's address. Behind `trusted_hops` proxies (Render: 1) X-Forwarded-For is read
    from the right, so a client cannot dodge the limit by sending its own header."""
    forwarded = request.headers.get("x-forwarded-for")
    if trusted_hops > 0 and forwarded:
        hops = [h.strip() for h in forwarded.split(",") if h.strip()]
        if len(hops) >= trusted_hops:
            return hops[-trusted_hops]
    return request.client.host if request.client else "unknown"


class MemoryCounter:
    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    async def add(self, key: str, weight: int) -> int:
        if len(self._counts) >= MAX_MEMORY_KEYS:
            current = _window()
            self._counts = {k: v for k, v in self._counts.items() if k.endswith(f":{current}")}
        self._counts[key] = self._counts.get(key, 0) + weight
        return self._counts[key]

    def clear(self) -> None:
        self._counts.clear()


class RedisCounter:
    """Shared counter; on error it is skipped for a cooldown and the memory one is used."""

    def __init__(self, url: str, fallback: MemoryCounter) -> None:
        self._client = redis.from_url(url, socket_timeout=0.5, socket_connect_timeout=0.5)
        self._fallback = fallback
        self._down_until = 0.0

    async def add(self, key: str, weight: int) -> int:
        if time.monotonic() < self._down_until:
            return await self._fallback.add(key, weight)
        try:
            async with self._client.pipeline(transaction=True) as pipe:
                pipe.incrby(KEY_PREFIX + key, weight)
                pipe.expire(KEY_PREFIX + key, WINDOW_SECONDS * 2)
                count, _ = await pipe.execute()
            return int(count)
        except Exception as exc:  # any Redis trouble: degrade, never block requests
            logger.warning("rate limit redis unavailable", extra={"error": type(exc).__name__})
            self._down_until = time.monotonic() + REDIS_COOLDOWN_SECONDS
            return await self._fallback.add(key, weight)


_memory = MemoryCounter()
_counters: dict[str, RedisCounter] = {}


def _window(now: float | None = None) -> int:
    return int((time.time() if now is None else now) // WINDOW_SECONDS)


def _counter(settings: Settings) -> MemoryCounter | RedisCounter:
    if not settings.redis_url:
        return _memory
    if settings.redis_url not in _counters:
        _counters[settings.redis_url] = RedisCounter(settings.redis_url, _memory)
    return _counters[settings.redis_url]


def reset_rate_limits() -> None:
    """Tests: forget every counter."""
    _memory.clear()
    _counters.clear()


def _is_internal(request: Request, settings: Settings) -> bool:
    key = settings.internal_api_key
    sent = request.headers.get(INTERNAL_KEY_HEADER, "")
    return bool(key) and hmac.compare_digest(sent.encode(), key.encode())


def _too_many(limit: int, retry_after: int) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "rate_limited",
                "message": "Çok fazla istek. Lütfen biraz sonra tekrar deneyin.",
            }
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": "0",
        },
    )


def install_rate_limit(app: FastAPI) -> None:
    @app.middleware("http")
    async def rate_limit(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        settings = get_settings()
        limit = settings.rate_limit_per_minute
        path = request.url.path
        if (
            limit <= 0
            or request.method == "OPTIONS"
            or path in EXEMPT_PATHS
            or _is_internal(request, settings)
        ):
            return await call_next(request)
        now = time.time()
        window = _window(now)
        ip = client_ip(request, settings.trusted_proxy_hops)
        if ip in LOOPBACK:
            return await call_next(request)
        used = await _counter(settings).add(f"{ip}:{window}", request_weight(path))
        if used > limit:
            retry_after = max(1, math.ceil((window + 1) * WINDOW_SECONDS - now))
            return _too_many(limit, retry_after)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - used))
        return response
