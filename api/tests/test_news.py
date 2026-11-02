from collections.abc import AsyncIterator
from datetime import UTC, datetime

import httpx
import pytest
import respx
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.football_data import FootballDataAdapter
from app.adapters.news_rss import FeedConfig, RssNewsAdapter, classify, parse_feed, plain_text
from app.core import cache
from app.core.config import Settings
from app.db.session import get_session
from app.main import create_app
from app.models import NewsArticle, NewsTag
from app.services.news_service import build_targets, find_tags, month_bounds, run_news_sync
from app.services.sync_service import run_sync

V1 = "/api/v1"
FEED = FeedConfig(name="test", url="https://example.com/rss", sport="football")

RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel>
<item><title>A &amp; B signs for Club</title><link>https://publisher.test/a</link>
<guid>1</guid><pubDate>Mon, 02 Nov 2026 08:30:00 +0200</pubDate>
<description><![CDATA[<p>Hello <b>world</b></p>]]></description>
<enclosure url="https://publisher.test/a.jpg" type="image/jpeg"/></item>
<item><title>No link</title></item>
<item><title>Bad scheme</title><link>javascript:alert(1)</link></item>
</channel></rss>"""

BOMB = """<?xml version="1.0"?>
<!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;&lol;">]>
<rss><channel><item><title>&lol2;</title><link>https://example.com/x</link></item></channel></rss>"""


def test_parse_rss_keeps_safe_links_and_strips_html() -> None:
    items = parse_feed(RSS, FEED)
    assert len(items) == 1
    item = items[0]
    assert item.title == "A & B signs for Club"
    assert item.summary == "Hello world"
    assert item.image_url is None  # publisher images are never kept
    assert item.published_at == datetime(2026, 11, 2, 6, 30, tzinfo=UTC)
    assert item.category == "transfer_official"
    assert item.source == "rss:test" and item.sport_slug == "football"


def test_entity_bombs_are_rejected() -> None:
    with pytest.raises(Exception, match="(?i)entit"):
        parse_feed(BOMB, FEED)


@pytest.mark.parametrize(
    ("title", "expected", "breaking"),
    [
        ("Son dakika: X resmen imzaladı", "transfer_official", True),
        ("İDDİA: Kulüp yıldız oyuncuyla ilgileniyor", "transfer_rumour", False),
        ("BREAKING: Player linked with move", "transfer_rumour", True),
        ("Interview: coach speaks about the season", "interview", False),
        ("Şampiyonlar Ligi kura çekimi yapıldı", "tournament", False),
        ("Maç ertelendi", "general", False),
    ],
)
def test_classify(title: str, expected: str, breaking: bool) -> None:
    assert classify(title, "", "general") == (expected, breaking)


def test_plain_text_truncates_on_word_boundary() -> None:
    text = plain_text("kelime " * 100, 20)
    assert text.endswith("…") and len(text) <= 21 and "kelim…" not in text


TARGETS = build_targets(
    [
        ("team_id", 1, "Chelsea FC", "Chelsea", None),
        ("team_id", 2, "Inter", None, None),
        ("team_id", 3, "Roma", None, None),
        ("team_id", 4, "Roma", None, None),  # shared team alias -> dropped
        ("player_id", 10, "Ali Can", None, 1),
        ("player_id", 11, "Ali Can", None, 2),  # same name, other team
        ("player_id", 12, "Pele", None, 1),  # single word -> never matched
        ("competition_id", 5, "Serie A", None, None),
    ]
)


def test_tags_aliases_and_word_boundaries() -> None:
    tags = find_tags("Chelsea beat Roma, Pele scored in Serie A", TARGETS)
    assert set(tags) == {("team_id", 1), ("competition_id", 5)}
    assert find_tags("Chelseas", TARGETS) == []


def test_shared_player_name_is_resolved_by_team() -> None:
    assert ("player_id", 11) in find_tags("Ali Can stars for Inter", TARGETS)
    assert not any(k == "player_id" for k, _ in find_tags("Ali Can stars", TARGETS))
    both = find_tags("Ali Can: Chelsea or Inter?", TARGETS)
    assert not any(k == "player_id" for k, _ in both)  # still ambiguous


def test_month_bounds() -> None:
    start, end = month_bounds("2026-12")
    assert (start.month, end.year, end.month) == (12, 2027, 1)
    with pytest.raises(ValueError):
        month_bounds("2026-13")


async def _seed_news(maker: async_sessionmaker[AsyncSession], settings: Settings) -> None:
    await run_sync(maker, FootballDataAdapter(settings), ("PL", "CL", "PD", "SA", "BL1"))
    run = await run_news_sync(maker, RssNewsAdapter(settings))
    assert run.status == "success", run.error


async def test_news_sync_is_idempotent_and_tags_entities(
    maker: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    await _seed_news(maker, settings)
    async with maker() as s:
        first = (
            await s.scalar(select(func.count()).select_from(NewsArticle)),
            await s.scalar(select(func.count()).select_from(NewsTag)),
        )
    await run_news_sync(maker, RssNewsAdapter(settings))
    async with maker() as s:
        second = (
            await s.scalar(select(func.count()).select_from(NewsArticle)),
            await s.scalar(select(func.count()).select_from(NewsTag)),
        )
    assert first == second
    assert first[0] == 17  # 9 + 5 + 3 valid items; the link-less one is skipped
    assert first[1] > 10


@pytest.fixture
async def news_client(seeded: async_sessionmaker, client: AsyncClient) -> AsyncClient:
    """The shared seeded database already holds the sample news (see conftest)."""
    await cache.get_cache().clear()
    return client


@pytest.fixture
async def writable_client(
    maker: async_sessionmaker[AsyncSession], settings: Settings
) -> AsyncIterator[AsyncClient]:
    """An app over a fresh database, for tests that write."""
    await _seed_news(maker, settings)
    application = create_app()

    async def override() -> AsyncIterator[AsyncSession]:
        async with maker() as s:
            yield s

    application.dependency_overrides[get_session] = override
    async with AsyncClient(transport=ASGITransport(app=application), base_url="http://t") as c:
        yield c


async def test_news_api_filters(news_client: AsyncClient) -> None:
    page = (await news_client.get(f"{V1}/news")).json()
    assert page["total"] == 17
    times = [i["published_at"] for i in page["items"]]
    assert times == sorted(times, reverse=True)

    transfer = (await news_client.get(f"{V1}/news", params={"category": "transfer"})).json()
    assert {i["category"] for i in transfer["items"]} == {"transfer_official", "transfer_rumour"}

    breaking = (await news_client.get(f"{V1}/news", params={"breaking": True})).json()
    assert breaking["total"] == 2 and all(i["is_breaking"] for i in breaking["items"])

    # Fixture dates follow the pinned "today", so the wall clock decides what is recent.
    recent = (await news_client.get(f"{V1}/news", params={"max_age_hours": 1})).json()
    assert recent["total"] <= page["total"]
    assert (await news_client.get(f"{V1}/news", params={"max_age_hours": 0})).status_code == 422

    football = (await news_client.get(f"{V1}/news", params={"sport": "football"})).json()
    assert football["total"] == 9  # basketball is not in the shared test database

    english = (await news_client.get(f"{V1}/news", params={"language": "en"})).json()
    assert english["total"] == 5


async def test_news_tagged_by_team_and_player(news_client: AsyncClient) -> None:
    page = (await news_client.get(f"{V1}/news", params={"q": "Jonas Demir"})).json()
    demir = next(t for i in page["items"] for t in i["tags"] if t["name"] == "Jonas Demir")
    by_player = (await news_client.get(f"{V1}/news", params={"player": demir["id"]})).json()
    # Only the item that also names Chelsea identifies which "Jonas Demir" it is.
    assert by_player["total"] == 1
    assert "Chelsea" in by_player["items"][0]["summary"]
    chelsea = next(t for i in by_player["items"] for t in i["tags"] if t["kind"] == "team")
    by_team = (await news_client.get(f"{V1}/news", params={"team": chelsea["id"]})).json()
    assert by_team["total"] >= 2
    comp = next(t for i in page["items"] for t in i["tags"] if t["kind"] == "competition")
    assert comp["slug"]


async def test_news_archive_and_month(news_client: AsyncClient) -> None:
    archive = (await news_client.get(f"{V1}/news/archive")).json()["months"]
    assert sum(m["count"] for m in archive) == 17
    assert [m["month"] for m in archive] == sorted((m["month"] for m in archive), reverse=True)
    month = archive[-1]["month"]
    page = (await news_client.get(f"{V1}/news", params={"month": month})).json()
    assert page["total"] == archive[-1]["count"]
    assert (await news_client.get(f"{V1}/news", params={"month": "2026-13"})).status_code == 422


async def test_news_detail_and_404(news_client: AsyncClient) -> None:
    first = (await news_client.get(f"{V1}/news")).json()["items"][0]
    detail = (await news_client.get(f"{V1}/news/{first['id']}")).json()
    assert detail["title"] == first["title"] and detail["source"]
    assert (await news_client.get(f"{V1}/news/999999")).status_code == 404


async def test_manual_news_requires_admin(
    writable_client: AsyncClient, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    news_client = writable_client
    body = {
        "title": "Son dakika: stat bakım için kapandı",
        "url": "https://example.com/duyuru",
        "category": "general",
        "sport": "football",
        "is_breaking": True,
    }
    assert (await news_client.post(f"{V1}/admin/news", json=body)).status_code in (401, 503)
    monkeypatch.setattr(
        "app.routers.admin.get_settings",
        lambda: settings.model_copy(update={"admin_token": "secret-token"}),
    )
    created = await news_client.post(
        f"{V1}/admin/news", json=body, headers={"X-Admin-Token": "secret-token"}
    )
    assert created.status_code == 201
    detail = (await news_client.get(f"{V1}/news/{created.json()['id']}")).json()
    assert detail["source"] == "manual" and detail["is_breaking"]
    bad = await news_client.post(
        f"{V1}/admin/news",
        json={**body, "url": "javascript:alert(1)"},
        headers={"X-Admin-Token": "secret-token"},
    )
    assert bad.status_code == 422


@respx.mock
async def test_live_feed_failure_is_recorded_not_fatal(
    maker: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    live = settings.model_copy(
        update={
            "data_mode": "live",
            "news_feeds": [
                {"name": "ok", "url": "https://feeds.example.com/ok"},
                {"name": "down", "url": "https://feeds.example.com/down"},
            ],
        }
    )
    respx.get("https://feeds.example.com/ok").mock(return_value=httpx.Response(200, text=RSS))
    respx.get("https://feeds.example.com/down").mock(return_value=httpx.Response(404))
    adapter = RssNewsAdapter(live)
    run = await run_news_sync(maker, adapter)
    await adapter.aclose()
    assert run.status == "partial" and run.items_upserted == 1
    assert "down" in (run.error or "")


@respx.mock
async def test_live_mode_drops_placeholder_links(
    maker: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    feed = RSS.replace("https://publisher.test/a", "https://www.example.com/story")
    live = settings.model_copy(
        update={"data_mode": "live", "news_feeds": [{"name": "x", "url": "https://p.test/rss"}]}
    )
    respx.get("https://p.test/rss").mock(return_value=httpx.Response(200, text=feed))
    adapter = RssNewsAdapter(live)
    assert await adapter.fetch() == []
    await adapter.aclose()


def test_three_word_names_also_match_their_last_two_words() -> None:
    targets = build_targets([("player_id", 7, "Andrea Kimi Antonelli", None, None)])
    assert find_tags("Kimi Antonelli crowned champion", targets) == [("player_id", 7)]
    assert find_tags("Antonelli crowned champion", targets) == []
