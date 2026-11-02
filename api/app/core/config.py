from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parents[2]
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
    news_feeds: list[dict[str, Any]] = Field(default_factory=list)
    news_interval_minutes: int = 15

    scheduler_enabled: bool = False
    sync_interval_minutes: int = 30
    cache_ttl_seconds: int = 60

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
