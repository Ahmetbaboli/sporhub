from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field
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
    app_version: str = "0.1.0"

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
    log_level: str = "info"

    # News feeds (JSON list): [{"name", "url", "sport", "category", "language"}]. See .env.example.
    news_feeds: list[dict[str, Any]] = Field(default_factory=lambda: list(DEFAULT_NEWS_FEEDS))
    news_interval_minutes: int = 15

    scheduler_enabled: bool = False
    cache_ttl_seconds: int = 60

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
