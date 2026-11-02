import httpx
import pytest
import respx
from httpx import AsyncClient

from app.core.config import Settings
from app.core.sources import SOURCES, probe_source, source_by_name, source_status

SECRET = "super-secret-key-value-123"


def test_status_reports_booleans_only(settings: Settings) -> None:
    configured = settings.model_copy(update={"football_data_api_key": SECRET})
    rows = {s.name: s for s in source_status(configured)}
    assert rows["football-data"].configured is True
    assert rows["thesportsdb"].configured is False
    assert rows["jolpica"].configured is True and rows["jolpica"].requires_key is False
    assert SECRET not in repr(source_status(configured))
    assert {s.name for s in SOURCES} >= {"football-data", "balldontlie", "jolpica", "news"}


@respx.mock
async def test_probe_calls_only_configured_sources(settings: Settings) -> None:
    route = respx.get("https://api.football-data.org/v4/competitions/PL").mock(
        return_value=httpx.Response(403)
    )
    async with httpx.AsyncClient() as client:
        empty = settings.model_copy(update={"football_data_api_key": ""})
        assert await probe_source(source_by_name("football-data"), empty, client) == []
        assert route.call_count == 0
        keyed = settings.model_copy(update={"football_data_api_key": SECRET})
        [result] = await probe_source(source_by_name("football-data"), keyed, client)
    assert route.calls.last.request.headers["X-Auth-Token"] == SECRET
    assert (result.ok, result.detail) == (False, "HTTP 403")
    assert SECRET not in repr(result)


@respx.mock
async def test_probe_news_feeds_one_request_each(settings: Settings) -> None:
    respx.get("https://feeds.example.org/a").mock(return_value=httpx.Response(200, text="<rss/>"))
    respx.get("https://feeds.example.org/b").mock(side_effect=httpx.ConnectTimeout("t"))
    feeds = [
        {"name": "a", "url": "https://feeds.example.org/a"},
        {"name": "b", "url": "https://feeds.example.org/b"},
    ]
    async with httpx.AsyncClient() as client:
        results = await probe_source(
            source_by_name("news"), settings.model_copy(update={"news_feeds": feeds}), client
        )
    assert [(r.target, r.ok, r.detail) for r in results] == [
        ("news:a", True, "HTTP 200"),
        ("news:b", False, "timeout"),
    ]


async def test_admin_sources_endpoint(
    client: AsyncClient, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert (await client.get("/api/v1/admin/sources")).status_code in (401, 503)
    patched = settings.model_copy(
        update={"admin_token": "admin-token", "balldontlie_api_key": SECRET}
    )
    monkeypatch.setattr("app.routers.admin.get_settings", lambda: patched)
    r = await client.get("/api/v1/admin/sources", headers={"X-Admin-Token": "admin-token"})
    assert r.status_code == 200
    rows = {row["name"]: row for row in r.json()}
    assert rows["balldontlie"]["configured"] is True
    assert SECRET not in r.text
    wrong = await client.get("/api/v1/admin/sources", headers={"X-Admin-Token": "nope"})
    assert wrong.status_code == 401
