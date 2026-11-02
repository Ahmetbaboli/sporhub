"""DATA_MODE guarantees: live never reads, writes or shows sample data; demo is labelled."""

import copy

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.football_data import FootballDataAdapter
from app.adapters.news_rss import RssNewsAdapter
from app.adapters.registry import adapter_names, create_adapter
from app.core.config import Settings
from app.core.data_mode import is_placeholder_url, record_source
from app.models import Competition, Event, NewsArticle, Player, Sport, SyncRun, Team
from app.scripts import seed
from app.services.demo_data import has_demo_rows, purge_demo
from app.services.news_service import run_news_sync
from app.services.sync_service import run_sync

SOURCED = (Competition, Team, Player, Event, NewsArticle)


def live(settings: Settings, **update: object) -> Settings:
    return settings.model_copy(
        update={
            "data_mode": "live",
            "football_data_api_key": "",
            "balldontlie_api_key": "",
            "news_feeds": [],
            **update,
        }
    )


async def _count(session: AsyncSession, model: type) -> int:
    return await session.scalar(select(func.count()).select_from(model)) or 0


@pytest.mark.parametrize("name", adapter_names())
async def test_live_without_key_writes_nothing(
    name: str, maker: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    adapter = create_adapter(name, live(settings))
    if adapter.configured:  # keyless sources (Jolpica) would hit the network here
        pytest.skip("source needs no key")
    run = await run_sync(maker, adapter)
    assert run.status == "skipped" and "anahtar" in (run.error or "")
    async with maker() as s:
        assert all([await _count(s, m) == 0 for m in SOURCED])
        assert await _count(s, SyncRun) == 1


async def test_live_news_without_feeds_reads_no_samples(
    maker: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    adapter = RssNewsAdapter(live(settings))
    assert adapter.feeds == [] and not adapter.use_fixtures
    await run_news_sync(maker, adapter)
    async with maker() as s:
        assert await _count(s, NewsArticle) == 0


@pytest.mark.parametrize("name", adapter_names())
def test_date_shift_never_runs_in_live_mode(name: str, settings: Settings) -> None:
    adapter = create_adapter(name, live(settings, fixture_today="2030-01-01"))
    payload = {
        "_fixture": {"reference_date": "2026-10-26"},
        "matches": [{"utcDate": "2026-10-26T15:00:00Z"}],
        "data": [{"date": "2026-10-26T15:00:00Z", "datetime": "2026-10-26T15:00:00Z"}],
        "MRData": {"RaceTable": {"Races": [{"date": "2026-10-26", "time": "15:00:00Z"}]}},
    }
    before = copy.deepcopy(payload)
    assert adapter._apply_date_shift(payload) == before  # type: ignore[attr-defined]


async def test_demo_rows_are_labelled_and_purge_keeps_real_rows(
    maker: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    demo = settings.model_copy(update={"data_mode": "demo"})
    await run_sync(maker, FootballDataAdapter(demo), ("PL",))
    await run_news_sync(maker, RssNewsAdapter(demo))
    async with maker() as s:
        sources = set((await s.scalars(select(Competition.source))).all())
        assert sources == {"demo:football-data"}
        news_sources = set((await s.scalars(select(NewsArticle.source))).all())
        assert all(src.startswith("demo:") for src in news_sources)
        # A real row from a live sync must survive the purge.
        sport_id = await s.scalar(select(Sport.id))
        s.add(Team(sport_id=sport_id, source="football-data", external_id="57", name="Real FC"))
        await s.commit()
        assert await has_demo_rows(s)

        counts = await purge_demo(s)
        assert counts["events"] > 0 and counts["news_articles"] > 0
        assert not await has_demo_rows(s)
        remaining = (await s.scalars(select(Team.name))).all()
        assert remaining == ["Real FC"]
        assert await _count(s, Event) == 0
        assert await purge_demo(s) == dict.fromkeys(counts, 0)  # idempotent


def test_record_source_and_placeholders(settings: Settings) -> None:
    assert record_source("jolpica", live(settings)) == "jolpica"
    assert record_source("jolpica", settings.model_copy(update={"data_mode": "demo"})) == (
        "demo:jolpica"
    )
    assert is_placeholder_url("https://example.com/x")
    assert is_placeholder_url("https://news.example.org/x")
    assert not is_placeholder_url("https://www.bbc.co.uk/sport")
    assert not is_placeholder_url("https://notexample.com/x")


async def test_seed_refuses_live_mode(monkeypatch: pytest.MonkeyPatch, settings: Settings) -> None:
    monkeypatch.setattr(seed, "get_settings", lambda: live(settings))
    with pytest.raises(SystemExit, match="DATA_MODE=demo"):
        await seed.seed()


async def test_meta_reports_mode_and_configuration(
    seeded: async_sessionmaker[AsyncSession], client, settings: Settings, monkeypatch
) -> None:
    body = (await client.get("/api/v1/meta")).json()
    assert body["data_mode"] == "demo"
    sports = {s["slug"]: s for s in body["sports"]}
    assert set(sports) == {"football", "basketball", "formula-1"}
    assert sports["formula-1"]["configured"] is True  # keyless
    assert sports["basketball"]["configured"] is False

    keyed = live(settings, balldontlie_api_key="k")
    monkeypatch.setattr("app.routers.v1.get_settings", lambda: keyed)
    body = (await client.get("/api/v1/meta")).json()
    assert body["data_mode"] == "live"
    assert {s["slug"]: s["configured"] for s in body["sports"]}["basketball"] is True
    sources = {s["name"]: s for s in body["sources"]}
    assert sources["football-data"]["last_success_at"]  # the seeded test sync
