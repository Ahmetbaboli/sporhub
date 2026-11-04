from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.espn_soccer import (
    EspnSoccerAdapter,
    map_status,
    normalize_standing,
    season_label,
    season_months,
    team_colors,
)
from app.adapters.football_data import FootballDataAdapter
from app.core.config import Settings
from app.models.catalog import Team
from app.services.sync_service import run_sync


def test_season_spans_july_to_june() -> None:
    months = season_months(2026)
    assert months[0] == "202607" and months[5] == "202612" and months[-1] == "202706"
    assert len(months) == 12 and season_label(2026) == "2026/27"


def test_status_prefers_specific_names_then_state() -> None:
    assert map_status({"type": {"name": "STATUS_POSTPONED", "state": "pre"}}) == "postponed"
    assert map_status({"type": {"name": "STATUS_FIRST_HALF", "state": "in"}}) == "live"
    assert map_status({"type": {"name": "STATUS_FULL_TIME", "state": "post"}}) == "finished"
    assert map_status({}) == "scheduled"


def test_standing_keeps_the_provider_zone() -> None:
    row = normalize_standing(
        {
            "team": {"id": "432", "displayName": "Galatasaray", "abbreviation": "GS"},
            "note": {"color": "#81D6AC", "description": "Champions League"},
            "stats": [
                {"name": "rank", "value": 1.0},
                {"name": "points", "value": 25.0},
                {"name": "pointDifferential", "value": 11.0},
            ],
        }
    )
    assert row.position == 1 and row.points == 25.0
    assert row.extra["zone"] == "Champions League" and row.extra["goal_difference"] == 11


def test_live_mode_is_opt_in(settings: Settings) -> None:
    live = settings.model_copy(update={"data_mode": "live"})
    assert EspnSoccerAdapter(live).configured is False
    assert EspnSoccerAdapter(live.model_copy(update={"espn_enabled": True})).configured


def test_team_colours_skip_espn_placeholder() -> None:
    assert team_colors({"color": "ffff00", "alternateColor": "ffffff"}) == {
        "color": "#ffff00",
        "alternate_color": "#ffffff",
    }
    assert team_colors({"color": "000000", "alternateColor": "C60000"}) == {
        "color": None,
        "alternate_color": None,
    }
    assert team_colors({"color": "000000", "alternateColor": "e91b23"})["color"] == "#000000"
    assert team_colors({"color": "not-a-colour"})["color"] is None


async def test_synced_teams_carry_real_colours_only(
    maker: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    await run_sync(maker, EspnSoccerAdapter(settings), ("tur.1",))
    async with maker() as s:
        rows = dict((await s.execute(select(Team.name, Team.color))).all())
    assert rows["Fenerbahce"] == "#ffff00" and rows["Galatasaray"] == "#aa0031"
    assert rows["Goztepe"] is None  # ESPN placeholder


async def test_colours_reach_a_club_first_created_by_another_source(
    maker: async_sessionmaker[AsyncSession], settings: Settings
) -> None:
    await run_sync(maker, FootballDataAdapter(settings), ("CL",))  # has Galatasaray, no colours
    await run_sync(maker, EspnSoccerAdapter(settings), ("tur.1",))
    async with maker() as s:
        rows = (
            await s.execute(select(Team.source, Team.color).where(Team.name.like("Galatasaray%")))
        ).all()
    assert rows == [("demo:football-data", "#aa0031")]  # one club, ESPN's colour
