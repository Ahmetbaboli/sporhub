"""Rate-limited, retrying JSON client shared by HTTP-based adapters."""

import asyncio
import logging
import time
from typing import Any

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 15.0
MAX_ATTEMPTS = 4
BACKOFF_MIN_SECONDS = 1.0
BACKOFF_MAX_SECONDS = 30.0
RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


class RetryableHTTPError(Exception):
    """Raised for responses worth retrying (429 / 5xx)."""


class RateLimitedClient:
    def __init__(
        self,
        base_url: str,
        headers: dict[str, str] | None = None,
        min_interval: float = 0.0,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        client: httpx.AsyncClient | None = None,
        backoff_min: float = BACKOFF_MIN_SECONDS,
    ) -> None:
        self._client = client or httpx.AsyncClient(
            base_url=base_url, headers=headers, timeout=timeout
        )
        self._min_interval = min_interval
        self._last_request = 0.0
        self._lock = asyncio.Lock()
        self._get = retry(
            retry=retry_if_exception_type((httpx.TransportError, RetryableHTTPError)),
            stop=stop_after_attempt(MAX_ATTEMPTS),
            wait=wait_exponential(min=backoff_min, max=BACKOFF_MAX_SECONDS),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )(self._get_once)

    async def _throttle(self) -> None:
        async with self._lock:
            wait = self._last_request + self._min_interval - time.monotonic()
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request = time.monotonic()

    async def _get_once(self, path: str, params: dict[str, Any] | None) -> Any:
        await self._throttle()
        response = await self._client.get(path, params=params)
        if response.status_code in RETRYABLE_STATUS:
            raise RetryableHTTPError(f"{path} -> HTTP {response.status_code}")
        response.raise_for_status()
        return response.json()

    async def get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        logger.info("external request", extra={"path": path})
        return await self._get(path, params)

    async def aclose(self) -> None:
        await self._client.aclose()
