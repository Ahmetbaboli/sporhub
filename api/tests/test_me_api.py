"""Authentication, authorization and behaviour of /api/v1/me (favorites + dashboard)."""

import time
from typing import Any

import jwt
import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.auth import AUDIENCE, ISSUER, MAX_TOKEN_LIFETIME_SECONDS
from app.models import Favorite, User
from tests.conftest import TOKEN_SECRET

ME = "/api/v1/me"


def make_token(sub: str = "github:1001", secret: str = TOKEN_SECRET, **overrides: Any) -> str:
    now = int(time.time())
    claims: dict[str, Any] = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "sub": sub,
        "name": "Ada Lovelace",
        "picture": "https://avatars.example/ada.png",
        "iat": now,
        "exp": now + 60,
        **overrides,
    }
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, secret, algorithm=overrides.pop("alg", "HS256"))


def auth(token: str | None = None, **kw: Any) -> dict[str, str]:
    return {"Authorization": f"Bearer {token or make_token(**kw)}"}


# ---- token verification -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Basic abc"},
        {"Authorization": "Bearer"},
        {"Authorization": "Bearer not-a-jwt"},
    ],
)
async def test_missing_or_malformed_credentials_are_401(client: AsyncClient, headers: dict) -> None:
    r = await client.get(ME, headers=headers)
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "unauthorized"


@pytest.mark.parametrize(
    ("label", "token"),
    [
        ("wrong secret", make_token(secret="x" * 48)),
        ("expired", make_token(iat=int(time.time()) - 600, exp=int(time.time()) - 300)),
        ("wrong audience", make_token(aud="someone-else")),
        ("wrong issuer", make_token(iss="evil-web")),
        ("lifetime too long", make_token(exp=int(time.time()) + MAX_TOKEN_LIFETIME_SECONDS + 3600)),
        ("no expiry", make_token(exp=None)),
        ("no subject", make_token(sub="")),
        ("subject without provider", make_token(sub="12345")),
    ],
)
async def test_invalid_tokens_are_rejected(client: AsyncClient, label: str, token: str) -> None:
    r = await client.get(ME, headers=auth(token))
    assert r.status_code == 401, label


async def test_unsigned_alg_none_token_is_rejected(client: AsyncClient) -> None:
    now = int(time.time())
    token = jwt.encode(
        {"iss": ISSUER, "aud": AUDIENCE, "sub": "github:1", "iat": now, "exp": now + 60},
        key=None,
        algorithm="none",
    )
    assert (await client.get(ME, headers=auth(token))).status_code == 401


async def test_account_endpoints_are_disabled_without_a_secret(
    client: AsyncClient, settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    disabled = settings.model_copy(update={"api_token_secret": ""})
    monkeypatch.setattr("app.core.auth.get_settings", lambda: disabled)
    r = await client.get(ME, headers=auth())
    assert r.status_code == 503 and r.json()["error"]["code"] == "auth_disabled"
    # public endpoints keep working
    assert (await client.get("/api/v1/sports")).status_code == 200


@pytest.mark.filterwarnings("ignore:The HMAC key")
async def test_short_secret_is_refused(
    client: AsyncClient, settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    weak = settings.model_copy(update={"api_token_secret": "short"})
    monkeypatch.setattr("app.core.auth.get_settings", lambda: weak)
    r = await client.get(ME, headers=auth(secret="short"))
    assert r.status_code == 503 and r.json()["error"]["code"] == "auth_misconfigured"


async def test_public_endpoints_do_not_need_a_token(client: AsyncClient) -> None:
    for path in ("/health", "/api/v1/sports", "/api/v1/search?q=arsenal"):
        assert (await client.get(path)).status_code == 200


# ---- user provisioning ------------------------------------------------------------------------


async def test_first_request_creates_the_user_and_later_ones_reuse_it(
    client: AsyncClient, seeded: async_sessionmaker
) -> None:
    first = (await client.get(ME, headers=auth(name="Ada"))).json()
    second = (await client.get(ME, headers=auth(name="Ada Lovelace"))).json()
    assert first["id"] == second["id"]
    assert second["display_name"] == "Ada Lovelace"  # profile refreshed from the token
    async with seeded() as s:
        assert await s.scalar(select(func.count()).select_from(User)) == 1


# ---- favorites ------------------------------------------------------------------------------


async def _first_team_id(client: AsyncClient) -> int:
    rows = (await client.get("/api/v1/competitions/premier-league/standings")).json()["items"]
    return rows[0]["team"]["id"]


async def test_add_list_and_remove_favorites(client: AsyncClient) -> None:
    team_id = await _first_team_id(client)
    h = auth()
    assert (await client.put(f"{ME}/favorites/teams/{team_id}", headers=h)).status_code == 204
    assert (await client.put(f"{ME}/favorites/competitions/1", headers=h)).status_code == 204
    player_id = (await client.get(f"/api/v1/teams/{team_id}")).json()["squad"][0]["id"]
    assert (await client.put(f"{ME}/favorites/players/{player_id}", headers=h)).status_code == 204

    ids = (await client.get(f"{ME}/favorites/ids", headers=h)).json()
    assert ids == {"teams": [team_id], "players": [player_id], "competitions": [1]}
    full = (await client.get(f"{ME}/favorites", headers=h)).json()
    assert full["teams"][0]["id"] == team_id and full["teams"][0]["name"]
    assert full["players"][0]["team"]["id"] == team_id
    assert full["competitions"][0]["slug"] == "premier-league"

    assert (await client.delete(f"{ME}/favorites/teams/{team_id}", headers=h)).status_code == 204
    assert (await client.get(f"{ME}/favorites/ids", headers=h)).json()["teams"] == []


async def test_put_is_idempotent_and_delete_of_unknown_is_a_noop(
    client: AsyncClient, seeded: async_sessionmaker
) -> None:
    team_id = await _first_team_id(client)
    h = auth()
    for _ in range(3):
        assert (await client.put(f"{ME}/favorites/teams/{team_id}", headers=h)).status_code == 204
    assert (await client.delete(f"{ME}/favorites/teams/999999", headers=h)).status_code == 204
    async with seeded() as s:
        assert await s.scalar(select(func.count()).select_from(Favorite)) == 1


async def test_favoriting_a_missing_entity_is_404_and_bad_kind_is_422(client: AsyncClient) -> None:
    h = auth()
    missing = await client.put(f"{ME}/favorites/teams/999999", headers=h)
    assert missing.status_code == 404
    assert (await client.put(f"{ME}/favorites/stadiums/1", headers=h)).status_code == 422


async def test_favorites_require_authentication(client: AsyncClient) -> None:
    team_id = await _first_team_id(client)
    for method, path in (
        ("GET", f"{ME}/favorites"),
        ("GET", f"{ME}/favorites/ids"),
        ("PUT", f"{ME}/favorites/teams/{team_id}"),
        ("DELETE", f"{ME}/favorites/teams/{team_id}"),
        ("GET", f"{ME}/dashboard"),
    ):
        assert (await client.request(method, path)).status_code == 401, (method, path)


async def test_users_cannot_see_or_remove_each_others_favorites(client: AsyncClient) -> None:
    team_id = await _first_team_id(client)
    alice, bob = auth(sub="github:1"), auth(sub="github:2")
    await client.put(f"{ME}/favorites/teams/{team_id}", headers=alice)
    await client.put(f"{ME}/favorites/competitions/1", headers=alice)

    # Bob sees nothing of Alice's...
    assert (await client.get(f"{ME}/favorites/ids", headers=bob)).json() == {
        "teams": [],
        "players": [],
        "competitions": [],
    }
    assert (await client.get(f"{ME}/dashboard", headers=bob)).json() == {
        "teams": [],
        "competitions": [],
    }
    # ...and deleting "the same" favorite as Bob does not touch Alice's.
    await client.delete(f"{ME}/favorites/teams/{team_id}", headers=bob)
    alice_ids = (await client.get(f"{ME}/favorites/ids", headers=alice)).json()
    assert alice_ids["teams"] == [team_id] and alice_ids["competitions"] == [1]


async def test_there_is_no_endpoint_to_read_another_users_data_by_id(client: AsyncClient) -> None:
    await client.get(ME, headers=auth(sub="github:1"))
    for path in ("/api/v1/users/1", "/api/v1/users/1/favorites", f"{ME}/1/favorites"):
        assert (await client.get(path, headers=auth(sub="github:2"))).status_code == 404


async def test_favorite_limit(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.services.me_service.MAX_FAVORITES_PER_USER", 1)
    h = auth()
    assert (await client.put(f"{ME}/favorites/competitions/1", headers=h)).status_code == 204
    r = await client.put(f"{ME}/favorites/competitions/2", headers=h)
    assert r.status_code == 409 and r.json()["error"]["code"] == "favorite_limit"


# ---- dashboard --------------------------------------------------------------------------------


async def test_dashboard_shows_favorite_team_events_and_league_position(
    client: AsyncClient,
) -> None:
    rows = (await client.get("/api/v1/competitions/premier-league/standings")).json()["items"]
    mid = rows[7]  # a team that is not in the top 5
    h = auth()
    await client.put(f"{ME}/favorites/teams/{mid['team']['id']}", headers=h)
    await client.put(f"{ME}/favorites/competitions/1", headers=h)

    data = (await client.get(f"{ME}/dashboard", headers=h)).json()
    (activity,) = data["teams"]
    assert activity["team"]["id"] == mid["team"]["id"]
    assert 1 <= len(activity["recent"]) <= 3 and 1 <= len(activity["upcoming"]) <= 3
    assert all(e["status"] == "finished" for e in activity["recent"])
    recent_times = [e["start_time"] for e in activity["recent"]]
    assert recent_times == sorted(recent_times, reverse=True)
    assert all(e["status"] in ("scheduled", "live") for e in activity["upcoming"])

    (place,) = data["competitions"]
    assert place["competition"]["slug"] == "premier-league"
    assert [r["position"] for r in place["table"]] == [1, 2, 3, 4, 5]
    assert [r["position"] for r in place["mine"]] == [8]
    assert place["mine"][0]["team"]["id"] == mid["team"]["id"]


# ---- lookup and per-entity endpoints used by the UI -----------------------------------------


async def test_team_and_player_lookups(client: AsyncClient) -> None:
    teams = (await client.get("/api/v1/teams", params={"sport": "football", "q": "arsen"})).json()
    assert [t["name"] for t in teams["items"]] == ["Arsenal FC"]
    players = (await client.get("/api/v1/players", params={"sport": "football", "limit": 5})).json()
    assert len(players["items"]) == 5
    assert (await client.get("/api/v1/teams", params={"limit": 1000})).status_code == 422


async def test_team_standings_entries_and_player_events(client: AsyncClient) -> None:
    team_id = await _first_team_id(client)
    entries = (await client.get(f"/api/v1/teams/{team_id}/standings")).json()["items"]
    assert {e["competition"]["slug"] for e in entries} >= {"premier-league"}
    assert all(e["standing"]["team"]["id"] == team_id for e in entries)
    assert (await client.get("/api/v1/teams/999999/standings")).status_code == 404
    pid = (await client.get(f"/api/v1/teams/{team_id}")).json()["squad"][0]["id"]
    # football fixtures list no players among participants: empty but valid
    assert (await client.get(f"/api/v1/players/{pid}/events")).json()["total"] == 0
    assert (await client.get("/api/v1/players/999999/events")).status_code == 404
