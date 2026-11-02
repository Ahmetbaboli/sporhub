from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SourceMeta(BaseModel):
    name: str
    sport: str | None
    configured: bool
    last_success_at: datetime | None = None
    last_attempt_at: datetime | None = None
    last_status: str | None = None
    # The last attempt failed after the last success, or the data is older than STALE_AFTER.
    stale: bool = False
    # The provider's plan delivers scores late: never present them as live.
    scores_delayed: bool = False


class SportMeta(BaseModel):
    slug: str
    name: str
    configured: bool  # at least one source for this sport is configured
    sources: list[str]


class NewsFeedMeta(BaseModel):
    name: str  # publisher, as credited on every card
    url: str  # the feed itself
    site: str  # publisher home page (scheme + host of the feed)
    language: str
    sport: str | None = None


class MetaOut(BaseModel):
    data_mode: Literal["live", "demo"]
    sports: list[SportMeta]
    sources: list[SourceMeta]
    news_feeds: list[NewsFeedMeta] = []


class BudgetWindow(BaseModel):
    limit: int
    used: int
    remaining: int


class SourceStatusDetail(SourceMeta):
    runs_24h: int = 0
    failures_24h: int = 0
    error_rate_24h: float = 0.0
    last_error: str | None = None
    budget: dict[str, BudgetWindow] = {}


class AdminStatus(BaseModel):
    data_mode: Literal["live", "demo"]
    scheduler_enabled: bool
    sources: list[SourceStatusDetail]
