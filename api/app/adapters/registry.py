"""Adapter registry. Adding a sport = write an adapter class + add one line below."""

from collections.abc import Callable

from app.adapters.balldontlie import BallDontLieAdapter
from app.adapters.base import BaseAdapter
from app.adapters.football_data import FootballDataAdapter
from app.adapters.jolpica import JolpicaAdapter
from app.core.config import Settings

AdapterFactory = Callable[[Settings], BaseAdapter]

ADAPTERS: dict[str, AdapterFactory] = {
    "football-data": FootballDataAdapter,
    "balldontlie": BallDontLieAdapter,
    "jolpica": JolpicaAdapter,
}


def adapter_names() -> list[str]:
    return sorted(ADAPTERS)


def create_adapter(name: str, settings: Settings) -> BaseAdapter:
    try:
        return ADAPTERS[name](settings)
    except KeyError:
        raise KeyError(f"Unknown adapter: {name}") from None
