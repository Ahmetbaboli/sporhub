"""Registry of external data sources: is each one configured, and can we reach it?

Only booleans and HTTP status codes ever leave this module — never a key value. Used by
GET /api/v1/admin/sources and `python -m app.scripts.check_sources`.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import httpx

from app.core.config import Settings

PROBE_TIMEOUT_SECONDS = 10.0
PROBE_USER_AGENT = "JustSport/0.4 (open-source sports data portfolio project)"

SourceKind = Literal["sports", "news"]


@dataclass(frozen=True)
class SourceSpec:
    name: str
    kind: SourceKind
    description: str
    requires_key: bool
    is_configured: Callable[[Settings], bool]
    sport: str | None  # sport slug it feeds; None for news
    # One cheap request proving the source answers with our configuration.
    probe_url: str
    probe_headers: Callable[[Settings], dict[str, str]]


SOURCES: tuple[SourceSpec, ...] = (
    SourceSpec(
        name="football-data",
        kind="sports",
        description="football-data.org v4 (futbol)",
        requires_key=True,
        sport="football",
        is_configured=lambda s: bool(s.football_data_api_key),
        probe_url="https://api.football-data.org/v4/competitions/PL",
        probe_headers=lambda s: {"X-Auth-Token": s.football_data_api_key},
    ),
    SourceSpec(
        name="thesportsdb",
        kind="sports",
        description="TheSportsDB v1 (Süper Lig, TFF 1. Lig; ücretli anahtar)",
        requires_key=True,
        sport="football",
        # The public development key "123" returns truncated data: not a live configuration.
        is_configured=lambda s: bool(s.thesportsdb_api_key) and s.thesportsdb_api_key != "123",
        probe_url="https://www.thesportsdb.com/api/v1/json/{key}/lookupleague.php?id=4339",
        probe_headers=lambda s: {},
    ),
    SourceSpec(
        name="balldontlie",
        kind="sports",
        description="balldontlie NBA v1 (basketbol)",
        requires_key=True,
        sport="basketball",
        is_configured=lambda s: bool(s.balldontlie_api_key),
        probe_url="https://api.balldontlie.io/v1/teams",
        probe_headers=lambda s: {"Authorization": s.balldontlie_api_key},
    ),
    SourceSpec(
        name="jolpica",
        kind="sports",
        description="Jolpica-F1, Ergast uyumlu (Formula 1)",
        requires_key=False,
        sport="formula-1",
        is_configured=lambda s: True,
        probe_url="https://api.jolpi.ca/ergast/f1/current/?limit=1",
        probe_headers=lambda s: {},
    ),
    SourceSpec(
        name="news",
        kind="news",
        description="RSS/Atom haber akışları (NEWS_FEEDS)",
        requires_key=False,
        sport=None,
        is_configured=lambda s: bool(s.news_feeds),
        probe_url="",  # probed per feed, see probe_news_feeds
        probe_headers=lambda s: {},
    ),
)


@dataclass(frozen=True)
class SourceStatus:
    name: str
    kind: SourceKind
    description: str
    requires_key: bool
    configured: bool


def source_status(settings: Settings) -> list[SourceStatus]:
    return [
        SourceStatus(s.name, s.kind, s.description, s.requires_key, s.is_configured(settings))
        for s in SOURCES
    ]


def source_by_name(name: str) -> SourceSpec:
    return next(s for s in SOURCES if s.name == name)


@dataclass(frozen=True)
class ProbeResult:
    target: str
    ok: bool
    detail: str  # "HTTP 200", "timeout", ... — never contains credentials


async def _probe(client: httpx.AsyncClient, target: str, url: str, headers: dict) -> ProbeResult:
    try:
        response = await client.get(url, headers={"User-Agent": PROBE_USER_AGENT, **headers})
    except httpx.TimeoutException:
        return ProbeResult(target, False, "timeout")
    except httpx.HTTPError as exc:
        return ProbeResult(target, False, type(exc).__name__)
    return ProbeResult(target, response.is_success, f"HTTP {response.status_code}")


async def probe_source(
    spec: SourceSpec, settings: Settings, client: httpx.AsyncClient
) -> list[ProbeResult]:
    """One request per source (one per feed for news). Unconfigured sources are not called."""
    if not spec.is_configured(settings):
        return []
    if spec.kind == "news":
        return [
            await _probe(client, f"news:{feed.get('name', '?')}", str(feed.get("url", "")), {})
            for feed in settings.news_feeds
        ]
    # Path-keyed APIs: the key is substituted here and never echoed back in results.
    url = spec.probe_url.replace("{key}", settings.thesportsdb_api_key)
    return [await _probe(client, spec.name, url, spec.probe_headers(settings))]
