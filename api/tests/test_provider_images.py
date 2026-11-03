from datetime import UTC, datetime

import pytest

from app.core.config import Settings
from app.models import NewsArticle
from app.services import read_service
from app.services.news_service import news_out
from app.services.read_service import provider_image

CREST = "https://crests.football-data.org/57.png"


def test_provider_images_are_hidden_by_default(settings: Settings) -> None:
    assert settings.show_provider_images is False
    assert provider_image(CREST) is None


def test_owner_can_opt_in_to_provider_images(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    opted_in = settings.model_copy(update={"show_provider_images": True})
    monkeypatch.setattr(read_service, "get_settings", lambda: opted_in)
    assert provider_image(CREST) == CREST
    assert provider_image(None) is None


def test_news_images_follow_the_same_switch(
    settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    article = NewsArticle(
        id=1,
        source="rss:t",
        title="t",
        summary="",
        url="https://publisher.test/a",
        image_url="https://publisher.test/a.jpg",
        category="general",
        is_breaking=False,
        language="tr",
        also_sources=[],
        tags=[],
        published_at=datetime(2026, 11, 3, tzinfo=UTC),
    )
    assert news_out(article).image_url is None
    opted_in = settings.model_copy(update={"show_provider_images": True})
    monkeypatch.setattr(read_service, "get_settings", lambda: opted_in)
    assert news_out(article).image_url == "https://publisher.test/a.jpg"


def test_nba_logos_come_from_an_explicit_code_table() -> None:
    from app.adapters.balldontlie import ESPN_LOGO_CODES, logo_url

    assert len(ESPN_LOGO_CODES) == 30
    assert logo_url("GSW") == "https://a.espncdn.com/i/teamlogos/nba/500/gs.png"
    assert logo_url("XYZ") is None and logo_url(None) is None
