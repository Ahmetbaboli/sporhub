"""News from RSS 2.0 / Atom feeds.

Only the headline, a short plain-text summary, the link and an optional image are kept: the
article itself stays on the publisher's site (we link to it, we never copy it). Feeds are
configured in NEWS_FEEDS (JSON list); in fixture mode fixtures/news/feeds.json is used.
XML is parsed with defusedxml (feeds are untrusted input: no entity expansion, no XXE).
"""

import hashlib
import html
import json
import logging
import re
from datetime import UTC, date, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Literal
from xml.etree.ElementTree import Element

import httpx
from defusedxml import DefusedXmlException, ElementTree
from pydantic import BaseModel, Field

from app.adapters.http import RateLimitedClient
from app.core.config import Settings

logger = logging.getLogger(__name__)

NewsCategory = Literal["general", "transfer_official", "transfer_rumour", "interview", "tournament"]
NEWS_CATEGORIES: tuple[str, ...] = (
    "general",
    "transfer_official",
    "transfer_rumour",
    "interview",
    "tournament",
)
SOURCE_PREFIX = "rss:"
SUMMARY_MAX_CHARS = 300
TITLE_MAX_CHARS = 300
MIN_FEED_INTERVAL_SECONDS = 1.0
FIXTURE_DIR = "news"
FIXTURE_INDEX = "feeds.json"

ATOM = "{http://www.w3.org/2005/Atom}"
MEDIA = "{http://search.yahoo.com/mrss/}"
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")

# Keyword rules, checked in priority order. Lower-cased (casefold) Turkish + English phrases.
OFFICIAL_WORDS = (
    "resmi", "resmen", "imzaladı", "imzayı attı", "kadrosuna kattı", "transferini açıkladı",
    "official", "has signed", "signs for", "completes move", "completes transfer", "unveiled",
)  # fmt: skip
RUMOUR_WORDS = (
    "söylenti", "iddia", "gündeminde", "ilgileniyor", "masada", "masasında", "listesinde",
    "transfer için",
    "rumour", "rumor", "linked with", "in talks", "eyeing", "monitoring", "interest in",
    "could join", "target",
)  # fmt: skip
INTERVIEW_WORDS = (
    "röportaj", "konuştu", "açıklamalarda bulundu", "anlattı",
    "interview", "speaks", "exclusive:", "q&a", "opens up",
)  # fmt: skip
TOURNAMENT_WORDS = (
    "kura", "turnuva", "organizasyon", "fikstür açıklandı", "ev sahipliği", "takvim açıklandı",
    "draw", "tournament", "fixtures announced", "host city", "hosts", "calendar announced",
)  # fmt: skip
BREAKING_PREFIXES = ("son dakika", "flaş", "breaking")


class FeedConfig(BaseModel):
    name: str
    url: str = ""
    sport: str | None = None  # sport slug, or None for multi-sport feeds
    category: NewsCategory = "general"  # used when no keyword rule matches
    language: str = "tr"
    file: str | None = None  # fixture mode only


class NewsDTO(BaseModel):
    source: str
    external_id: str
    url: str
    title: str
    summary: str = ""
    image_url: str | None = None
    author: str | None = None
    published_at: datetime
    category: NewsCategory = "general"
    is_breaking: bool = False
    language: str = "tr"
    sport_slug: str | None = None
    keywords: list[str] = Field(default_factory=list)


def plain_text(value: str | None, limit: int = SUMMARY_MAX_CHARS) -> str:
    """Strip markup and entities; cut at a word boundary with an ellipsis."""
    text = SPACE_RE.sub(" ", html.unescape(TAG_RE.sub(" ", value or ""))).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return f"{cut}…"


def _has(text: str, words: tuple[str, ...]) -> bool:
    return any(w in text for w in words)


def fold(text: str) -> str:
    """Case-insensitive form; Turkish İ folds to plain i (casefold would add a dot)."""
    return text.replace("İ", "i").casefold()


def classify(title: str, summary: str, default: NewsCategory) -> tuple[NewsCategory, bool]:
    """(category, is_breaking) from keywords; falls back to the feed's category."""
    text = f"{fold(title)} {fold(summary)}"
    breaking = fold(title).lstrip("🔴 ").startswith(BREAKING_PREFIXES)
    if _has(text, OFFICIAL_WORDS):
        return "transfer_official", breaking
    if _has(text, RUMOUR_WORDS):
        return "transfer_rumour", breaking
    if _has(text, INTERVIEW_WORDS):
        return "interview", breaking
    if _has(text, TOURNAMENT_WORDS):
        return "tournament", breaking
    return default, breaking


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    try:
        parsed = parsedate_to_datetime(value)  # RFC 822 (RSS)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))  # RFC 3339 (Atom)
        except ValueError:
            return None
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)).astimezone(UTC)


def _text(node: Element | None, path: str) -> str | None:
    found = node.find(path) if node is not None else None
    return found.text if found is not None and found.text else None


def _external_id(feed: FeedConfig, guid: str | None, link: str) -> str:
    key = guid or link
    return hashlib.sha256(f"{feed.name}|{key}".encode()).hexdigest()[:40]


def _rss_image(item: Element) -> str | None:
    enclosure = item.find("enclosure")
    if enclosure is not None and enclosure.get("type", "").startswith("image/"):
        return enclosure.get("url")
    # Elements with no children are falsy, so compare with None explicitly.
    media = item.find(f"{MEDIA}content")
    if media is None:
        media = item.find(f"{MEDIA}thumbnail")
    return media.get("url") if media is not None else None


def _build(
    feed: FeedConfig,
    *,
    guid: str | None,
    link: str | None,
    title: str | None,
    summary: str | None,
    published: datetime | None,
    image: str | None,
    author: str | None,
) -> NewsDTO | None:
    if not link or not title or not link.startswith(("http://", "https://")):
        return None
    clean_title = plain_text(title, TITLE_MAX_CHARS)
    clean_summary = plain_text(summary)
    category, breaking = classify(clean_title, clean_summary, feed.category)
    return NewsDTO(
        source=f"{SOURCE_PREFIX}{feed.name}",
        external_id=_external_id(feed, guid, link),
        url=link,
        title=clean_title,
        summary=clean_summary,
        image_url=image if image and image.startswith("https://") else None,
        author=plain_text(author, 120) or None,
        published_at=published or datetime.now(UTC),
        category=category,
        is_breaking=breaking,
        language=feed.language,
        sport_slug=feed.sport,
    )


def parse_feed(xml_text: str, feed: FeedConfig) -> list[NewsDTO]:
    """RSS 2.0 (<item>) or Atom (<entry>) into NewsDTOs; malformed entries are skipped."""
    root = ElementTree.fromstring(xml_text)
    items: list[NewsDTO | None] = []
    for item in root.iter("item"):
        items.append(
            _build(
                feed,
                guid=_text(item, "guid"),
                link=_text(item, "link"),
                title=_text(item, "title"),
                summary=_text(item, "description"),
                published=_parse_date(_text(item, "pubDate")),
                image=_rss_image(item),
                author=_text(item, "author")
                or _text(item, "{http://purl.org/dc/elements/1.1/}creator"),
            )
        )
    for entry in root.iter(f"{ATOM}entry"):
        link = next(
            (
                el.get("href")
                for el in entry.findall(f"{ATOM}link")
                if el.get("rel", "alternate") == "alternate"
            ),
            None,
        )
        items.append(
            _build(
                feed,
                guid=_text(entry, f"{ATOM}id"),
                link=link,
                title=_text(entry, f"{ATOM}title"),
                summary=_text(entry, f"{ATOM}summary") or _text(entry, f"{ATOM}content"),
                published=_parse_date(
                    _text(entry, f"{ATOM}published") or _text(entry, f"{ATOM}updated")
                ),
                image=None,
                author=_text(entry, f"{ATOM}author/{ATOM}name"),
            )
        )
    return [i for i in items if i is not None]


class RssNewsAdapter:
    """Fetches every configured feed; one failing feed is logged and skipped."""

    source = "news"

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self.use_fixtures = settings.use_fixtures
        self._fixtures = settings.fixtures_dir / FIXTURE_DIR
        self._fixture_today = (
            date.fromisoformat(settings.fixture_today) if settings.fixture_today else None
        )
        self.feeds = (
            self._fixture_feeds()
            if self.use_fixtures
            else [FeedConfig.model_validate(f) for f in settings.news_feeds]
        )
        self._http = (
            None
            if self.use_fixtures
            else RateLimitedClient("", min_interval=MIN_FEED_INTERVAL_SECONDS, client=client)
        )
        self.errors: list[str] = []

    def _fixture_index(self) -> dict:
        return json.loads((self._fixtures / FIXTURE_INDEX).read_text(encoding="utf-8"))

    def _fixture_feeds(self) -> list[FeedConfig]:
        return [FeedConfig.model_validate(f) for f in self._fixture_index()["feeds"]]

    def _fixture_shift(self) -> timedelta:
        reference = self._fixture_index().get("_fixture", {}).get("reference_date")
        if not reference:
            return timedelta(0)
        today = self._fixture_today or datetime.now(UTC).date()
        return timedelta(days=(today - date.fromisoformat(reference)).days)

    async def _read(self, feed: FeedConfig) -> str:
        if self._http is None:
            return (self._fixtures / str(feed.file)).read_text(encoding="utf-8")
        return await self._http.get_text(feed.url)

    async def fetch(self) -> list[NewsDTO]:
        shift = self._fixture_shift() if self.use_fixtures else timedelta(0)
        news: list[NewsDTO] = []
        for feed in self.feeds:
            try:
                items = parse_feed(await self._read(feed), feed)
            except (
                httpx.HTTPError,
                ElementTree.ParseError,
                DefusedXmlException,
                OSError,
                ValueError,
            ) as exc:
                logger.warning("feed failed", extra={"feed": feed.name, "error": str(exc)})
                self.errors.append(f"{feed.name}: {exc}")
                continue
            for item in items:
                item.published_at += shift
            news.extend(items)
        return news

    async def aclose(self) -> None:
        if self._http:
            await self._http.aclose()
