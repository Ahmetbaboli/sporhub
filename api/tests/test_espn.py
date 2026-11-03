from app.adapters.espn_soccer import (
    EspnSoccerAdapter,
    map_status,
    normalize_standing,
    season_label,
    season_months,
)
from app.core.config import Settings


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
