"""Shared plumbing for adapters that read a JSON HTTP API or, in fixture mode, local files."""

import json
import logging
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from app.adapters.base import BaseAdapter
from app.adapters.budget import get_budget
from app.adapters.http import RateLimitedClient
from app.core.config import Settings
from app.core.data_mode import is_demo, record_source

logger = logging.getLogger(__name__)

FIXTURE_META_KEY = "_fixture"
FIXTURE_REFERENCE_KEY = "reference_date"


class SourceNotConfiguredError(RuntimeError):
    """Raised when a live adapter without its API key is asked for data."""

    def __init__(self, source: str) -> None:
        super().__init__(f"{source}: API key not configured")


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
        self.use_fixtures = is_demo(settings)
        self.record_source = record_source(self.source, settings)
        # Live mode never falls back to sample data: a missing key means "not configured".
        self.configured = self.use_fixtures or not (self.requires_api_key and not api_key)
        if not self.configured:
            logger.warning("API key missing; source not configured", extra={"source": self.source})
        self._http: RateLimitedClient | None = None
        if self.configured and not self.use_fixtures:
            self._http = RateLimitedClient(
                self.base_url,
                headers=headers,
                min_interval=min_interval,
                client=client,
                budget=get_budget(self.source),
            )

    async def _request(self, path: str, fixture: str, params: dict[str, Any] | None = None) -> Any:
        if self.use_fixtures:
            return self._load_fixture(fixture)
        if self._http is None:
            raise SourceNotConfiguredError(self.source)
        return await self._http.get_json(path, params)

    def _load_fixture(self, name: str) -> Any:
        data = json.loads((self._fixtures_dir / f"{name}.json").read_text(encoding="utf-8"))
        return self._apply_date_shift(data)

    def _apply_date_shift(self, data: Any) -> Any:
        """Demo mode only: move sample dates so the sample 'today' is the real today."""
        if not self.use_fixtures:  # never touch real responses
            return data
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
