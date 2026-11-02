"""Rate-limited, retrying JSON client shared by HTTP-based adapters."""

import asyncio
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx
from tenacity import (
    RetryCallState,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.adapters.budget import RequestBudget

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 15.0
MAX_ATTEMPTS = 4
BACKOFF_MIN_SECONDS = 1.0
BACKOFF_MAX_SECONDS = 30.0
RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
TOO_MANY_REQUESTS = 429
# A Retry-After longer than this aborts the request instead of blocking a sync.
MAX_RETRY_AFTER_SECONDS = 120.0


class RetryableHTTPError(Exception):
    """Raised for responses worth retrying (429 / 5xx)."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


def parse_retry_after(value: str | None) -> float | None:
    """Retry-After is either delta-seconds or an HTTP date."""
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    return max(0.0, (when - datetime.now(UTC)).total_seconds())


def _wait_strategy(backoff_min: float) -> Callable[[RetryCallState], float]:
    exponential = wait_exponential(min=backoff_min, max=BACKOFF_MAX_SECONDS)

    def wait(state: RetryCallState) -> float:
        exc = state.outcome.exception() if state.outcome else None
        retry_after = getattr(exc, "retry_after", None)
        if retry_after is not None:
            return min(retry_after, MAX_RETRY_AFTER_SECONDS)
        return exponential(state)

    return wait


class RateLimitedClient:
    def __init__(
        self,
        base_url: str,
        headers: dict[str, str] | None = None,
        min_interval: float = 0.0,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        client: httpx.AsyncClient | None = None,
        backoff_min: float = BACKOFF_MIN_SECONDS,
        budget: RequestBudget | None = None,
    ) -> None:
        self._budget = budget
        self._client = client or httpx.AsyncClient(
            base_url=base_url, headers=headers, timeout=timeout
        )
        self._min_interval = min_interval
        self._last_request = 0.0
        self._lock = asyncio.Lock()
        self._get = retry(
            retry=retry_if_exception_type((httpx.TransportError, RetryableHTTPError)),
            stop=stop_after_attempt(MAX_ATTEMPTS),
            wait=_wait_strategy(backoff_min),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )(self._get_once)

    async def _throttle(self) -> None:
        async with self._lock:
            wait = self._last_request + self._min_interval - time.monotonic()
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request = time.monotonic()

    async def _get_once(self, path: str, params: dict[str, Any] | None) -> httpx.Response:
        if self._budget is not None:
            await self._budget.acquire()  # raises BudgetExhaustedError instead of overspending
        await self._throttle()
        response = await self._client.get(path, params=params)
        if response.status_code in RETRYABLE_STATUS:
            retry_after = parse_retry_after(response.headers.get("Retry-After"))
            if response.status_code == TOO_MANY_REQUESTS:
                logger.warning("rate limited", extra={"path": path, "retry_after": retry_after})
                if self._budget is not None and retry_after:
                    self._budget.pause(retry_after)
            raise RetryableHTTPError(f"{path} -> HTTP {response.status_code}", retry_after)
        response.raise_for_status()
        return response

    async def get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        logger.info("external request", extra={"path": path})
        return (await self._get(path, params)).json()

    async def get_text(self, path: str, params: dict[str, Any] | None = None) -> str:
        """Raw body (RSS/Atom feeds); same throttle, timeout and retry policy as JSON."""
        logger.info("external request", extra={"path": path})
        return (await self._get(path, params)).text

    async def aclose(self) -> None:
        await self._client.aclose()
