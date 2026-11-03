import pytest

from app.core.config import Settings
from app.services import read_service
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
