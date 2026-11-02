"""Masking configured secrets wherever text can leave the process (logs, stored error messages).

Some providers carry the key in the URL path (TheSportsDB), and httpx error messages include the
full URL — so every log line and every sync_runs.error is passed through `redact`.
"""

from app.core.config import Settings, get_settings

SECRET_FIELDS = (
    "football_data_api_key",
    "thesportsdb_api_key",
    "balldontlie_api_key",
    "admin_token",
    "api_token_secret",
)
# Shorter values (e.g. TheSportsDB's public development key "123") are not secrets and masking
# them would corrupt ordinary numbers in log lines.
MIN_SECRET_LENGTH = 8
MASK = "***"


def secret_values(settings: Settings) -> list[str]:
    values = (str(getattr(settings, name, "") or "") for name in SECRET_FIELDS)
    return sorted({v for v in values if len(v) >= MIN_SECRET_LENGTH}, key=len, reverse=True)


def redact(text: str, settings: Settings | None = None) -> str:
    for value in secret_values(settings or get_settings()):
        text = text.replace(value, MASK)
    return text
