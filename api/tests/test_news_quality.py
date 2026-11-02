"""Classifier quality on real headlines, the no-full-text rule, duplicate merging, feed list."""

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.news_rss import (
    SUMMARY_MAX_CHARS,
    FeedConfig,
    NewsDTO,
    classify,
    parse_feed,
    short_summary,
)
from app.core.config import DEFAULT_NEWS_FEEDS, Settings
from app.core.data_mode import is_placeholder_url
from app.models import NewsArticle
from app.services.news_service import _Tagger, save_article, similarity

DATA = Path(__file__).parent / "data" / "real_headlines_2026-11-02.json"
MIN_ACCURACY = 0.9


def test_classifier_on_real_headlines() -> None:
    items = json.loads(DATA.read_text(encoding="utf-8"))["items"]
    assert len(items) >= 100
    predicted = [(x["category"], classify(x["title"], "", "general")[0]) for x in items]
    accuracy = sum(a == b for a, b in predicted) / len(predicted)
    assert accuracy >= MIN_ACCURACY, accuracy
    # "Official transfer" must never be claimed without an explicit official phrase.
    false_official = Counter(a for a, b in predicted if b == "transfer_official" and a != b)
    assert not false_official


@pytest.mark.parametrize(
    "title",
    [
        "Were any current Man City players signed during charges period?",
        "Transfer rumors, news: Real Madrid believe Man Utd's JJ Gabriel will sign for them",
        "Edwards and others join the dreaded injury list",
    ],
)
def test_never_official(title: str) -> None:
    assert classify(title, "", "general")[0] != "transfer_official"


ARTICLE = " ".join(f"Sentence number {i} of the full article text." for i in range(40))
RSS = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>
<item><title>Club confirms new coach</title><link>https://publisher.test/a</link>
<description>{ARTICLE}</description>
<content:encoded><![CDATA[<p>{ARTICLE}</p><img src="https://publisher.test/i.jpg"/>]]></content:encoded>
<enclosure url="https://publisher.test/i.jpg" type="image/jpeg"/></item>
</channel></rss>"""
ATOM = f"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><entry>
<title>Long read</title><link href="https://publisher.test/b"/><id>b</id>
<updated>2026-11-02T10:00:00Z</updated><content type="html">{ARTICLE}</content></entry></feed>"""


def test_full_text_and_images_are_never_kept() -> None:
    feed = FeedConfig(name="t", url="https://publisher.test/rss")
    [rss] = parse_feed(RSS, feed)
    assert (
        rss.summary
        == "Sentence number 0 of the full article text. Sentence number 1 of the full article text."
    )
    assert len(rss.summary) <= SUMMARY_MAX_CHARS and rss.image_url is None
    assert "Sentence number 2" not in rss.model_dump_json()
    [atom] = parse_feed(ATOM, feed)
    assert atom.summary == ""  # Atom <content> is the article itself: ignored


def test_verbatim_feeds_are_whole_or_nothing() -> None:
    assert short_summary("One. Two. Three.", "verbatim_or_none") == "One. Two. Three."
    assert short_summary(ARTICLE, "verbatim_or_none") == ""


def test_windows_1254_feed_is_decoded() -> None:
    xml = (
        '<?xml version="1.0" encoding="windows-1254"?><rss><channel><item>'
        "<title>Beşiktaş'ta Rıdvan Yılmaz rüzgarı</title><link>https://publisher.test/c</link>"
        "</item></channel></rss>"
    ).encode("cp1254")
    [item] = parse_feed(xml, FeedConfig(name="s", url="https://publisher.test"))
    assert item.title == "Beşiktaş'ta Rıdvan Yılmaz rüzgarı"


def test_similarity() -> None:
    a = "Antonelli becomes world champion as Verstappen wins in Mexico"
    assert similarity(a, "Verstappen wins in Mexico as Antonelli becomes world champion") == 1
    assert similarity(a, "Arsenal move clear at the top with a rare win at Liverpool") < 0.2
    assert similarity("Short title", "Short title") == 0  # too few words to judge


def _dto(source: str, title: str, url: str) -> NewsDTO:
    return NewsDTO(
        source=source, external_id=url[-8:], url=url, title=title,
        published_at=datetime(2026, 11, 2, 10, tzinfo=UTC), language="en",
    )  # fmt: skip


async def test_same_story_from_two_publishers_is_merged(
    maker: async_sessionmaker[AsyncSession],
) -> None:
    async with maker() as s:
        tagger = _Tagger(s)
        first = await save_article(
            s,
            _dto(
                "rss:BBC Sport",
                "Antonelli becomes world champion as Verstappen wins in Mexico",
                "https://bbc.test/1",
            ),
            None,
            tagger,
        )
        merged = await save_article(
            s, _dto("rss:ESPN", "Verstappen wins in Mexico; Antonelli becomes world champion",
                    "https://espn.test/2"), None, tagger)  # fmt: skip
        other = await save_article(
            s, _dto("rss:ESPN", "Hamilton says Ferrari need serious talks after Mexico",
                    "https://espn.test/3"), None, tagger)  # fmt: skip
        await s.commit()
        assert merged == first and other != first
        assert await s.scalar(select(func.count()).select_from(NewsArticle)) == 2
        story = await s.get(NewsArticle, first)
        assert story is not None
        assert story.also_sources == [{"source": "ESPN", "url": "https://espn.test/2"}]


def test_default_feeds_are_real_publishers(settings: Settings) -> None:
    assert Settings(data_mode="live").news_feeds == DEFAULT_NEWS_FEEDS
    langs = Counter(f["language"] for f in DEFAULT_NEWS_FEEDS)
    sports = {f["sport"] for f in DEFAULT_NEWS_FEEDS}
    assert langs["tr"] >= 2 and langs["en"] >= 3
    assert {"football", "basketball", "formula-1"} <= sports
    for feed in DEFAULT_NEWS_FEEDS:
        assert feed["url"].startswith("https://") and not is_placeholder_url(feed["url"])
