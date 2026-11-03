"""News from RSS 2.0 / Atom feeds.

Only the headline, a short plain-text summary, the link and the feed's own image URL are
kept: the article itself stays on the publisher's site (we link to it, we never copy it). The
image is never downloaded; the API serves its URL only with SHOW_PROVIDER_IMAGES=true. Feeds are
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
from app.core.data_mode import is_demo, is_placeholder_url, record_source

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
CONTENT = "{http://purl.org/rss/1.0/modules/content/}"
IMG_SRC = re.compile(r"<img[^>]+src=[\"'](https://[^\"']+)[\"']", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


# Headline rules (casefolded text, word-boundary regexes), checked in priority order:
# rumour BEFORE official ("…believe X will sign for them" is a rumour), then interview, then
# tournament/organisation. Tuned on 140 real hand-labelled headlines
# (tests/data/real_headlines_2026-11-02.json); results are in docs/DECISIONS.md.
def _rx(*patterns: str) -> re.Pattern[str]:
    return re.compile("|".join(rf"(?<!\w)(?:{p})(?!\w)" for p in patterns))


RUMOUR_RX = _rx(
    r"söylenti\w*", r"iddia\w*", r"gündemin\w*", r"ilgileniyor", r"ilgilen\w+", r"peşinde",
    r"masa(?:da|sında)", r"listesinde", r"transfer haberi", r"teklif\w*", r"radarında",
    r"rumou?rs?", r"gossip", r"papers", r"linked", r"eyes?", r"eyeing", r"keen",
    r"monitoring", r"interest(?:ed)?(?: in)?", r"in talks", r"could (?:join|sign|leave)",
    r"set to (?:join|sign|leave|raid)", r"close to (?:joining|signing)", r"want(?:s)?",
    r"reportedly", r"believe", r"transfer target", r"bid for",
)  # fmt: skip
OFFICIAL_RX = _rx(
    r"resm(?:en|i olarak|î olarak)", r"imzaladı", r"imzayı attı", r"kadrosuna kattı",
    r"transferini açıkladı", r"ile anlaştı", r"göreve getirildi", r"sözleşme(?:si)? uzatıldı",
    r"officially", r"ha(?:s|ve) signed", r"signs? (?:for|with|new deal)", r"signed for",
    r"completes? (?:move|transfer|signing)", r"(?:to )?joins?(?= (?!the\b))", r"appoints?",
    r"appointed",
    r"new deal", r"contract extension", r"done deals", r"pick up (?:team )?options",
    r"unveiled",
)  # fmt: skip
INTERVIEW_RX = _rx(
    r"röportaj\w*", r"konuştu", r"açıklama\w*", r"yorumu", r"anlattı", r"sözler\w*",
    r"interview", r"exclusive with", r"q&a", r"opens up", r"says", r"speaks",
)  # fmt: skip
# A quotation of at least two words: double quotes anywhere (Turkish style), single quotes only
# at the start or after a colon ("Ten Hag on X: 'From …'"). One-word scare quotes ('lucky') and
# possessives ("Man Utd's") are not quotations; apostrophes inside words ("it's") are allowed.
_IN_QUOTE = r"(?:[^\"'”’‘“]|(?<=\w)['’](?=\w))"
QUOTE_RX = re.compile(
    rf"[\"“]{_IN_QUOTE}+\s{_IN_QUOTE}+[\"”]"
    rf"|(?:^|:\s*)['‘]{_IN_QUOTE}+\s{_IN_QUOTE}+['’](?!\w)"
)
# BBC style attribution: "F1 has never had anyone like me - Hamilton".
ATTRIBUTION_RX = re.compile(r"\s[-–]\s[A-ZÇĞİÖŞÜ][\w'’.]+$")
TOURNAMENT_RX = _rx(
    r"kura\w*", r"turnuva\w*", r"organizasyon\w*", r"fikstür\w*", r"takvim\w*", r"hakem\w*",
    r"ev sahipliği\w*", r"tören\w*", r"geri sayım",
    r"draw", r"tournament", r"fixtures announced", r"schedule", r"calendar",
    r"host(?:s|ed|ing)?", r"season start",
)  # fmt: skip
BREAKING_PREFIXES = ("son dakika", "flaş", "breaking")


class FeedConfig(BaseModel):
    name: str
    url: str = ""
    sport: str | None = None  # sport slug, or None for multi-sport feeds
    category: NewsCategory = "general"  # used when no keyword rule matches
    language: str = "tr"
    # "sentences": the feed's own summary cut to MAX_SUMMARY_SENTENCES.
    # "verbatim_or_none": publishers that forbid modification (Yahoo) - whole or nothing.
    summary: Literal["sentences", "verbatim_or_none"] = "sentences"
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


SENTENCE_END_RE = re.compile(r"(?<=[.!?…])\s+(?=[\"'“‘(]?[A-ZÇĞİÖŞÜ0-9])")
MAX_SUMMARY_SENTENCES = 2


def short_summary(value: str | None, policy: str = "sentences") -> str:
    """At most two sentences of the feed's own summary (never the article itself).

    "verbatim_or_none" keeps the text untouched or drops it when it is too long to show.
    """
    text = plain_text(value, limit=10_000)
    if policy == "verbatim_or_none":
        return text if len(text) <= SUMMARY_MAX_CHARS else ""
    sentences = SENTENCE_END_RE.split(text)
    return plain_text(" ".join(sentences[:MAX_SUMMARY_SENTENCES]))


def plain_text(value: str | None, limit: int = SUMMARY_MAX_CHARS) -> str:
    """Strip markup and entities; cut at a word boundary with an ellipsis."""
    text = SPACE_RE.sub(" ", html.unescape(TAG_RE.sub(" ", value or ""))).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return f"{cut}…"


def fold(text: str) -> str:
    """Case-insensitive form; Turkish İ folds to plain i (casefold would add a dot)."""
    return text.replace("İ", "i").casefold()


def classify(title: str, summary: str, default: NewsCategory) -> tuple[NewsCategory, bool]:
    """(category, is_breaking) from the headline; falls back to the feed's category.

    Only the headline is used: summaries mention transfers/quotes in passing far too often.
    """
    del summary  # kept in the signature for callers; see docstring
    text = fold(title)
    breaking = text.lstrip("🔴 ").startswith(BREAKING_PREFIXES)
    if RUMOUR_RX.search(text):
        return "transfer_rumour", breaking
    # A question is never a confirmation ("Were any players signed…?").
    if OFFICIAL_RX.search(text) and not text.rstrip().endswith("?"):
        return "transfer_official", breaking
    if INTERVIEW_RX.search(text) or QUOTE_RX.search(title) or ATTRIBUTION_RX.search(title):
        return "interview", breaking
    if TOURNAMENT_RX.search(text):
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


def _embedded_image(item: Element) -> str | None:
    """Some feeds (Sporx, Yahoo) put the story's picture in the HTML of the description or
    content:encoded; take the first https <img src> address only, never the HTML itself."""
    for tag in ("description", f"{CONTENT}encoded"):
        match = IMG_SRC.search(_text(item, tag) or "")
        if match:
            return html.unescape(match.group(1))
    return None


def _rss_image(item: Element) -> str | None:
    enclosure = item.find("enclosure")
    if enclosure is not None and enclosure.get("type", "").startswith("image/"):
        return enclosure.get("url")
    # Elements with no children are falsy, so compare with None explicitly.
    media = item.find(f"{MEDIA}content")
    if media is None:
        media = item.find(f"{MEDIA}thumbnail")
    if media is not None and media.get("url"):
        return media.get("url")
    return _embedded_image(item)


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
    clean_summary = short_summary(summary, feed.summary)
    category, breaking = classify(clean_title, clean_summary, feed.category)
    return NewsDTO(
        source=f"{SOURCE_PREFIX}{feed.name}",
        external_id=_external_id(feed, guid, link),
        url=link,
        title=clean_title,
        summary=clean_summary,
        # The feed's own picture for this story (URL only, https only); shown by the API only
        # when the owner opted in (SHOW_PROVIDER_IMAGES), as several feeds restrict reuse.
        image_url=image if image and image.startswith("https://") else None,
        author=plain_text(author, 120) or None,
        published_at=published or datetime.now(UTC),
        category=category,
        is_breaking=breaking,
        language=feed.language,
        sport_slug=feed.sport,
    )


def parse_feed(xml_text: str | bytes, feed: FeedConfig) -> list[NewsDTO]:
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
                # <content> is the full article: never used, only the summary.
                summary=_text(entry, f"{ATOM}summary"),
                published=_parse_date(
                    _text(entry, f"{ATOM}published") or _text(entry, f"{ATOM}updated")
                ),
                image=_rss_image(entry),
                author=_text(entry, f"{ATOM}author/{ATOM}name"),
            )
        )
    return [i for i in items if i is not None]


class RssNewsAdapter:
    """Fetches every configured feed; one failing feed is logged and skipped."""

    source = "news"

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self.use_fixtures = is_demo(settings)
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

    async def _read(self, feed: FeedConfig) -> bytes:
        # Bytes, so the XML declaration decides the encoding (Sporx is windows-1254).
        if self._http is None:
            return (self._fixtures / str(feed.file)).read_bytes()
        return await self._http.get_bytes(feed.url)

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
                # Live mode never stores placeholder links (sample data, broken feeds).
                if not self.use_fixtures and is_placeholder_url(item.url):
                    continue
                item.published_at += shift
                item.source = record_source(item.source, self._settings)
                news.append(item)
        return news

    async def aclose(self) -> None:
        if self._http:
            await self._http.aclose()
