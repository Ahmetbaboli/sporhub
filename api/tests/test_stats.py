import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.jolpica import JolpicaAdapter
from app.core import cache
from app.core.config import Settings
from app.repositories import queries
from app.services.stats_service import get_player_stats, race_leaders, race_summary
from app.services.sync_service import run_sync

V1 = "/api/v1"


@pytest.fixture(autouse=True)
async def _clear_cache() -> None:
    await cache.get_cache().clear()


async def test_football_stats_summary_is_consistent(
    seeded: async_sessionmaker, client: AsyncClient
) -> None:
    r = await client.get(f"{V1}/competitions/premier-league/stats")
    assert r.status_code == 200
    body = r.json()
    m = body["matches"]
    assert m["played"] > 0
    assert m["home_win_pct"] + m["draw_pct"] + m["away_win_pct"] == pytest.approx(1, abs=0.02)
    assert m["avg_per_match"] == pytest.approx(m["total_scored"] / m["played"], abs=0.01)
    assert body["races"] is None
    assert body["history"] and body["history"][0]["leader"]["position"] == 1


async def test_football_leaders(seeded: async_sessionmaker, client: AsyncClient) -> None:
    body = (await client.get(f"{V1}/competitions/premier-league/stats")).json()
    boards = {c["key"]: c for c in body["leaders"]}
    assert {"goals", "assists", "best_attack", "best_defence"} <= set(boards)
    goals = boards["goals"]["rows"]
    assert boards["goals"]["subject"] == "player" and goals[0]["rank"] == 1
    assert [g["value"] for g in goals] == sorted((g["value"] for g in goals), reverse=True)
    assert all(g["player"] and g["team"] for g in goals)
    defence = [r["value"] for r in boards["best_defence"]["rows"]]
    assert defence == sorted(defence)
    # Ties share a rank.
    for prev, row in zip(goals, goals[1:], strict=False):
        assert (row["rank"] == prev["rank"]) == (row["value"] == prev["value"])


async def test_unknown_competition_stats_is_404(
    seeded: async_sessionmaker, client: AsyncClient
) -> None:
    assert (await client.get(f"{V1}/competitions/nope/stats")).status_code == 404


async def test_f1_race_leaders(maker: async_sessionmaker[AsyncSession], settings: Settings) -> None:
    adapter = JolpicaAdapter(settings)
    await run_sync(maker, adapter, adapter.default_competitions)
    async with maker() as s:
        comp = (await queries.list_competitions(s, "formula-1"))[0]
        season = await queries.current_season(s, comp.id)
        assert season is not None
        events = await queries.list_season_events(s, season.id)
    summary = race_summary(events)
    assert summary is not None and summary.completed > 0
    boards = {b.key: b for b in race_leaders(events)}
    assert {"wins", "podiums", "avg_finish"} <= set(boards)
    assert sum(r.value for r in boards["wins"].rows) == summary.completed
    finish = [r.value for r in boards["avg_finish"].rows]
    assert finish == sorted(finish)


async def test_football_player_stats_from_scorers(
    seeded: async_sessionmaker, client: AsyncClient
) -> None:
    body = (await client.get(f"{V1}/competitions/premier-league/stats")).json()
    top = next(c for c in body["leaders"] if c["key"] == "goals")["rows"][0]
    r = await client.get(f"{V1}/players/{top['player']['id']}/stats")
    assert r.status_code == 200
    items = r.json()["items"]
    pl = next(i for i in items if i["competition"]["slug"] == "premier-league")
    assert pl["stats"]["goals"] == top["value"]
    assert pl["stats"]["goals_per_match"] == pytest.approx(
        pl["stats"]["goals"] / pl["stats"]["played"], abs=0.01
    )


async def test_player_stats_unknown_is_404(seeded: async_sessionmaker, client: AsyncClient) -> None:
    assert (await client.get(f"{V1}/players/999999/stats")).status_code == 404


async def test_driver_season_stats(
    maker: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    adapter = JolpicaAdapter(settings)
    await run_sync(maker, adapter, adapter.default_competitions)
    async with maker() as s:
        comp = (await queries.list_competitions(s, "formula-1"))[0]
        season = await queries.current_season(s, comp.id)
        assert season is not None
        leader = next(
            r for r in await queries.list_standings(s, season.id) if r.player_id is not None
        )
        stats = await get_player_stats(s, leader.player_id)
    sheet = stats.items[0].stats
    assert 0 < sheet["race_points"] <= leader.points  # standings add sprint points
    assert sheet["wins"] == leader.won
    assert sheet["podiums"] >= sheet["wins"]
    assert 1 <= sheet["best_finish"] <= sheet["avg_finish"]
