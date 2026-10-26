from functools import lru_cache
from pathlib import Path

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
    use_fixtures: bool = True
    fixtures_dir: Path = DEFAULT_FIXTURES_DIR
    # Pins "today" for fixture date shifting (YYYY-MM-DD); used by tests.
    fixture_today: str = ""

    admin_token: str = Field(default="", repr=False)
    cors_origins: str = "http://localhost:3000"
    log_level: str = "info"

    scheduler_enabled: bool = False
    sync_interval_minutes: int = 30
    cache_ttl_seconds: int = 60

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
