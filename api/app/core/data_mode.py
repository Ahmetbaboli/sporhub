"""Live vs demo data.

* live (default): only real provider data. Fixtures are never read, never written, never shown.
* demo: bundled fixtures + sample news; every row they produce is stored with a `demo:`
  source prefix so it can always be told apart from real data and purged.
"""

from urllib.parse import urlsplit

from app.core.config import Settings

DEMO_PREFIX = "demo:"
# Hosts reserved for documentation (RFC 2606); real content never links there.
PLACEHOLDER_HOSTS = ("example.com", "example.org", "example.net")


def is_demo(settings: Settings) -> bool:
    return settings.data_mode == "demo"


def record_source(source: str, settings: Settings) -> str:
    """The `source` value stored in the database for rows coming from `source`."""
    return f"{DEMO_PREFIX}{source}" if is_demo(settings) else source


def display_source(stored: str) -> str:
    return stored.removeprefix(DEMO_PREFIX)


def is_placeholder_url(url: str) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return any(host == h or host.endswith(f".{h}") for h in PLACEHOLDER_HOSTS)
