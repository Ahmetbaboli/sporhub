from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core import cache

V1 = "/api/v1"


@pytest.fixture(autouse=True)
async def _data(seeded: async_sessionmaker) -> None:
    await cache.get_cache().clear()


async def test_health(client: AsyncClient) -> None:
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_openapi_is_served(client: AsyncClient) -> None:
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    assert f"{V1}/search" in r.json()["paths"]


async def test_sports_and_competitions(client: AsyncClient) -> None:
    sports = (await client.get(f"{V1}/sports")).json()
    assert [s["slug"] for s in sports["items"]] == ["football"]
    comps = (await client.get(f"{V1}/sports/football/competitions")).json()
    assert {c["slug"] for c in comps["items"]} == {"premier-league", "uefa-champions-league"}


async def test_unknown_sport_uses_error_envelope(client: AsyncClient) -> None:
    r = await client.get(f"{V1}/sports/curling/competitions")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


async def test_competition_by_slug_and_id(client: AsyncClient) -> None:
    by_slug = (await client.get(f"{V1}/competitions/premier-league")).json()
    assert by_slug["current_season"]["year_label"] == "2026/27"
    by_id = (await client.get(f"{V1}/competitions/{by_slug['id']}")).json()
    assert by_id["slug"] == "premier-league"


async def test_competition_events_pagination_and_filters(client: AsyncClient) -> None:
    r = await client.get(
        f"{V1}/competitions/premier-league/events",
        params={"status": "finished", "page_size": 25, "order": "desc"},
    )
    body = r.json()
    assert body["total"] == 84 and len(body["items"]) == 25 and body["page"] == 1
    times = [datetime.fromisoformat(e["start_time"]) for e in body["items"]]
    assert times == sorted(times, reverse=True)
    assert all(e["status"] == "finished" for e in body["items"])
    page4 = (
        await client.get(
            f"{V1}/competitions/premier-league/events",
            params={"status": "finished", "page_size": 25, "page": 4},
        )
    ).json()
    assert len(page4["items"]) == 9


async def test_competition_events_date_range(client: AsyncClient) -> None:
    r = await client.get(
        f"{V1}/competitions/premier-league/events",
        params={"from": "2026-10-26", "to": "2026-10-26"},
    )
    items = r.json()["items"]
    assert items and all(e["start_time"].startswith("2026-10-26") for e in items)


async def test_standings(client: AsyncClient) -> None:
    rows = (await client.get(f"{V1}/competitions/premier-league/standings")).json()["items"]
    assert len(rows) == 20
    assert rows[0]["position"] == 1 and rows[0]["team"]["name"]
    assert rows[0]["points"] >= rows[1]["points"]


async def test_today_events_in_requested_timezone(client: AsyncClient) -> None:
    r = await client.get(
        f"{V1}/events/today",
        params={"sport": "football", "date": "2026-10-26", "tz": "Europe/Istanbul"},
    )
    items = r.json()["items"]
    assert items
    first = items[0]
    assert first["competition"]["sport_slug"] == "football"
    assert {p["side"] for p in first["participants"]} == {"home", "away"}


async def test_today_rejects_bad_timezone(client: AsyncClient) -> None:
    r = await client.get(f"{V1}/events/today", params={"tz": "Mars/Base"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_timezone"


async def test_event_detail_and_404(client: AsyncClient) -> None:
    listing = (await client.get(f"{V1}/competitions/premier-league/events")).json()
    event_id = listing["items"][0]["id"]
    assert (await client.get(f"{V1}/events/{event_id}")).json()["id"] == event_id
    missing = await client.get(f"{V1}/events/999999")
    assert missing.status_code == 404
    assert set(missing.json()["error"]) == {"code", "message"}


async def test_team_squad_and_events(client: AsyncClient) -> None:
    standings = (await client.get(f"{V1}/competitions/premier-league/standings")).json()["items"]
    team_id = standings[0]["team"]["id"]
    team = (await client.get(f"{V1}/teams/{team_id}")).json()
    assert len(team["squad"]) == 15
    events = (await client.get(f"{V1}/teams/{team_id}/events")).json()
    assert events["total"] >= 9
    assert all(team_id in {p["team"]["id"] for p in e["participants"]} for e in events["items"])


async def test_player(client: AsyncClient) -> None:
    team = (await client.get(f"{V1}/teams/1")).json()
    pid = team["squad"][0]["id"]
    player = (await client.get(f"{V1}/players/{pid}")).json()
    assert player["team"]["id"] == 1


async def test_search(client: AsyncClient) -> None:
    r = (await client.get(f"{V1}/search", params={"q": "arsenal"})).json()
    assert [t["name"] for t in r["teams"]] == ["Arsenal FC"]
    league = (await client.get(f"{V1}/search", params={"q": "premier"})).json()
    assert league["competitions"][0]["slug"] == "premier-league"


async def test_search_validation(client: AsyncClient) -> None:
    short = await client.get(f"{V1}/search", params={"q": "a"})
    assert short.status_code == 422 and short.json()["error"]["code"] == "query_too_short"
    missing = await client.get(f"{V1}/search")
    assert missing.status_code == 422 and missing.json()["error"]["code"] == "validation_error"


async def test_responses_are_cached(client: AsyncClient, seeded: async_sessionmaker) -> None:
    await client.get(f"{V1}/sports")
    assert await cache.get_cache().get("sports") is not None


async def test_admin_sync_requires_token(client: AsyncClient) -> None:
    no_token = await client.post(f"{V1}/admin/sync/football-data")
    assert no_token.status_code == 401
    wrong = await client.post(f"{V1}/admin/sync/football-data", headers={"X-Admin-Token": "x"})
    assert wrong.status_code == 401
    unknown = await client.post(
        f"{V1}/admin/sync/nope", headers={"X-Admin-Token": "test-admin-token"}
    )
    assert unknown.status_code == 404


async def test_admin_sync_accepts_valid_token(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    called: list[str] = []

    async def fake(name: str) -> None:
        called.append(name)

    monkeypatch.setattr("app.routers.admin._sync_in_background", fake)
    r = await client.post(
        f"{V1}/admin/sync/football-data", headers={"X-Admin-Token": "test-admin-token"}
    )
    assert r.status_code == 202
    assert called == ["football-data"]
