"""Shared plumbing for adapters that read a JSON HTTP API or, in fixture mode, local files."""

import json
import logging
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from app.adapters.base import BaseAdapter
from app.adapters.http import RateLimitedClient
from app.core.config import Settings

logger = logging.getLogger(__name__)

FIXTURE_META_KEY = "_fixture"
FIXTURE_REFERENCE_KEY = "reference_date"


class HttpFixtureAdapter(BaseAdapter):
    """Adds a rate-limited HTTP client and the fixture mode every adapter must support.

    Subclasses declare `fixtures_subdir`, implement `shift_fixture_dates` for their payload
    shape, and call `self._request(path, fixture_name, params)` for every endpoint.
    """

    fixtures_subdir: str
    base_url: str
    requires_api_key: bool = True

    def __init__(
        self,
        settings: Settings,
        *,
        api_key: str = "",
        headers: dict[str, str] | None = None,
        min_interval: float = 0.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._fixtures_dir: Path = settings.fixtures_dir / self.fixtures_subdir
        self._fixture_today = (
            date.fromisoformat(settings.fixture_today) if settings.fixture_today else None
        )
        missing_key = self.requires_api_key and not api_key
        self.use_fixtures = settings.use_fixtures or missing_key
        self.fell_back_to_fixtures = self.use_fixtures and not settings.use_fixtures
        if self.fell_back_to_fixtures:
            logger.warning(
                "API key missing; falling back to fixtures", extra={"source": self.source}
            )
        self._http: RateLimitedClient | None = None
        if not self.use_fixtures:
            self._http = RateLimitedClient(
                self.base_url, headers=headers, min_interval=min_interval, client=client
            )

    async def _request(self, path: str, fixture: str, params: dict[str, Any] | None = None) -> Any:
        if self._http is None:
            return self._load_fixture(fixture)
        return await self._http.get_json(path, params)

    def _load_fixture(self, name: str) -> Any:
        data = json.loads((self._fixtures_dir / f"{name}.json").read_text(encoding="utf-8"))
        return self._apply_date_shift(data)

    def _apply_date_shift(self, data: Any) -> Any:
        """Fixture mode only: move sample dates so the sample 'today' is the real today."""
        reference = (data.get(FIXTURE_META_KEY) or {}).get(FIXTURE_REFERENCE_KEY)
        if not reference:
            return data
        today = self._fixture_today or datetime.now(UTC).date()
        delta = timedelta(days=(today - date.fromisoformat(reference)).days)
        self.shift_fixture_dates(data, delta)
        return data

    def shift_fixture_dates(self, data: Any, delta: timedelta) -> None:
        """Mutate `data` in place, adding `delta` to every date/time the source reports."""
        raise NotImplementedError

    async def aclose(self) -> None:
        if self._http:
            await self._http.aclose()
