from functools import lru_cache
from pathlib import Path
from typing import Any, Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parents[2]

# Publisher-run feeds whose terms allow showing headline + short summary + link with attribution
# (audit with quotes and URLs: docs/DATA-SOURCES.md, 2026-11-02). Override with NEWS_FEEDS.
DEFAULT_NEWS_FEEDS: list[dict[str, Any]] = [
    {"name": "BBC Sport", "url": "https://feeds.bbci.co.uk/sport/football/rss.xml",
     "sport": "football", "language": "en"},
    {"name": "BBC Sport", "url": "https://feeds.bbci.co.uk/sport/formula1/rss.xml",
     "sport": "formula-1", "language": "en"},
    {"name": "BBC Sport", "url": "https://feeds.bbci.co.uk/sport/basketball/rss.xml",
     "sport": "basketball", "language": "en"},
    {"name": "ESPN", "url": "https://www.espn.com/espn/rss/soccer/news",
     "sport": "football", "language": "en"},
    {"name": "ESPN", "url": "https://www.espn.com/espn/rss/nba/news",
     "sport": "basketball", "language": "en"},
    {"name": "ESPN", "url": "https://www.espn.com/espn/rss/f1/news",
     "sport": "formula-1", "language": "en"},
    {"name": "Yahoo Sports", "url": "https://sports.yahoo.com/nba/rss/",
     "sport": "basketball", "language": "en", "summary": "verbatim_or_none"},
    {"name": "Habertürk", "url": "https://www.haberturk.com/rss/spor.xml",
     "sport": None, "language": "tr"},
    {"name": "Sporx", "url": "https://www.sporx.com/_xml/rss.php",
     "sport": None, "language": "tr"},
]  # fmt: skip
DEFAULT_FIXTURES_DIR = API_ROOT / "fixtures"


class Settings(BaseSettings):
    """Application settings, read from environment variables (see api/.env.example)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Just Sport API"
    app_version: str = "0.4.0"

    database_url: str = "postgresql+asyncpg://justsport:justsport@localhost:5432/justsport"
    redis_url: str = ""

    football_data_api_key: str = Field(default="", repr=False)
    balldontlie_api_key: str = Field(default="", repr=False)
    thesportsdb_api_key: str = Field(default="", repr=False)
    # live = real provider data only; demo = bundled fixtures + sample news, clearly labelled.
    data_mode: Literal["live", "demo"] = "live"
    fixtures_dir: Path = DEFAULT_FIXTURES_DIR
    # Pins "today" for demo-mode fixture date shifting (YYYY-MM-DD); used by tests.
    fixture_today: str = ""

    admin_token: str = Field(default="", repr=False)
    # HS256 key shared with the web app (API_TOKEN_SECRET); empty disables /api/v1/me.
    api_token_secret: str = Field(default="", repr=False)
    cors_origins: str = "http://localhost:3000"
    # Requests per minute per client IP (heavy endpoints count more); 0 turns the limit off.
    rate_limit_per_minute: int = 120
    # Shared with the web server (same value in web/.env); its requests skip the limit.
    internal_api_key: str = Field(default="", repr=False)
    # Proxies in front of the API that append to X-Forwarded-For (Render: 1; direct: 0).
    trusted_proxy_hops: int = 0
    log_level: str = "info"

    # News feeds (JSON list): [{"name", "url", "sport", "category", "language"}]. See .env.example.
    news_feeds: list[dict[str, Any]] = Field(default_factory=lambda: list(DEFAULT_NEWS_FEEDS))
    news_interval_minutes: int = 15

    scheduler_enabled: bool = False
    cache_ttl_seconds: int = 60
    # Serve provider crest/logo URLs; only after the owner has the display right.
    show_provider_images: bool = False
    # Opt-in: ESPN's unofficial, keyless site API for the Süper Lig (personal use).
    espn_enabled: bool = False

    @field_validator("database_url")
    @classmethod
    def _asyncpg_url(cls, value: str) -> str:
        return normalize_database_url(value)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


# libpq options that asyncpg does not understand (Neon/Render copy-paste URLs carry them).
_LIBPQ_ONLY = {"channel_binding", "sslmode"}


def normalize_database_url(url: str) -> str:
    """'postgres://…?sslmode=require' (Neon) -> 'postgresql+asyncpg://…?ssl=require'."""
    parts = urlsplit(url)
    scheme = parts.scheme
    if scheme in ("postgres", "postgresql"):
        scheme = "postgresql+asyncpg"
    if not scheme.startswith("postgresql"):
        return url
    query = dict(parse_qsl(parts.query))
    sslmode = query.pop("sslmode", None)
    for key in _LIBPQ_ONLY:
        query.pop(key, None)
    if sslmode and sslmode != "disable" and "ssl" not in query:
        query["ssl"] = "require"
    return urlunsplit((scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


@lru_cache
def get_settings() -> Settings:
    return Settings()
