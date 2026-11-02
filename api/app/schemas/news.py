from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

from app.adapters.news_rss import NewsCategory
from app.schemas.api import Page

TagKind = Literal["team", "player", "competition"]


class NewsTagOut(BaseModel):
    kind: TagKind
    id: int
    name: str
    sport_slug: str | None = None
    slug: str | None = None  # competitions only (web route)


class NewsOut(BaseModel):
    id: int
    title: str
    summary: str
    url: str
    image_url: str | None = None
    author: str | None = None
    source: str  # display name of the feed / "manual"
    published_at: datetime
    category: NewsCategory
    is_breaking: bool
    language: str
    sport_slug: str | None = None
    tags: list[NewsTagOut] = Field(default_factory=list)


class NewsList(Page[NewsOut]):
    pass


class ArchiveMonth(BaseModel):
    month: str  # YYYY-MM (UTC)
    count: int


class NewsArchive(BaseModel):
    months: list[ArchiveMonth]


class ManualNewsIn(BaseModel):
    """Editor-written item (admin). The link may point to our own page or a publisher."""

    title: str = Field(min_length=5, max_length=300)
    url: HttpUrl
    summary: str = Field(default="", max_length=300)
    category: NewsCategory = "general"
    sport: str | None = None
    is_breaking: bool = False
    language: Literal["tr", "en"] = "tr"
    published_at: datetime | None = None


class ManualNewsCreated(BaseModel):
    id: int
