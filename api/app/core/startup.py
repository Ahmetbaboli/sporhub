"""Fail fast, and readably, when the environment is wrong.

Messages name the variable and the rule - never the value (it may be a secret).
"""

from pydantic import ValidationError

from app.core.config import Settings

MIN_ADMIN_TOKEN_LENGTH = 16
MIN_API_TOKEN_SECRET_LENGTH = 32
PLACEHOLDER_ADMIN_TOKENS = frozenset({"change-me", "changeme", "admin", "secret"})
DEVELOPMENT_KEYS = {"thesportsdb_api_key": "123"}


class ConfigurationError(RuntimeError):
    pass


def describe_validation_error(exc: ValidationError) -> str:
    """Pydantic's own message echoes input values; keep only field names and reasons."""
    lines = [
        f"  - {'.'.join(str(p) for p in err['loc']).upper()}: {err['msg']}" for err in exc.errors()
    ]
    return "Ortam değişkenleri geçersiz:\n" + "\n".join(lines)


def check_settings(settings: Settings) -> tuple[list[str], list[str]]:
    """(errors, warnings). Errors stop the app; warnings are logged."""
    errors: list[str] = []
    warnings: list[str] = []
    if settings.admin_token and (
        settings.admin_token.lower() in PLACEHOLDER_ADMIN_TOKENS
        or len(settings.admin_token) < MIN_ADMIN_TOKEN_LENGTH
    ):
        errors.append(
            f"ADMIN_TOKEN örnek değerde veya {MIN_ADMIN_TOKEN_LENGTH} karakterden kısa; "
            "rastgele uzun bir değer verin ya da boş bırakın (admin uçları kapanır)."
        )
    if settings.api_token_secret and len(settings.api_token_secret) < MIN_API_TOKEN_SECRET_LENGTH:
        errors.append(
            f"API_TOKEN_SECRET en az {MIN_API_TOKEN_SECRET_LENGTH} karakter olmalı "
            "(web uygulamasındakiyle aynı değer)."
        )
    if settings.internal_api_key and len(settings.internal_api_key) < MIN_API_TOKEN_SECRET_LENGTH:
        errors.append(
            f"INTERNAL_API_KEY en az {MIN_API_TOKEN_SECRET_LENGTH} karakter olmalı "
            "(web sunucusundakiyle aynı değer)."
        )
    if settings.rate_limit_per_minute > 0 and not settings.internal_api_key:
        warnings.append(
            "RATE_LIMIT_PER_MINUTE açık ama INTERNAL_API_KEY boş: web sunucusunun istekleri de "
            "sınırlanır; yoğun trafikte site 429 alabilir."
        )
    if "*" in settings.cors_origin_list:
        errors.append("CORS_ORIGINS '*' içeremez; web sitesinin tam adresini yazın.")
    for i, feed in enumerate(settings.news_feeds):
        url = str(feed.get("url", ""))
        if not feed.get("name") or not url.startswith("https://"):
            errors.append(f"NEWS_FEEDS[{i}]: 'name' ve https ile başlayan 'url' zorunlu.")
    if settings.data_mode == "live":
        if not settings.news_feeds:
            warnings.append(
                "NEWS_FEEDS boş liste: haber çekilmez. Varsayılan akışlar için satırı silin."
            )
        if settings.database_url.startswith("sqlite"):
            warnings.append(
                "DATA_MODE=live ama DATABASE_URL SQLite: yalnızca yerel geliştirme için."
            )
        for field, dev_value in DEVELOPMENT_KEYS.items():
            if getattr(settings, field) == dev_value:
                warnings.append(
                    f"{field.upper()} herkese açık geliştirme anahtarı; "
                    "canlıda yapılandırılmamış sayılır."
                )
        if settings.scheduler_enabled and not any(
            getattr(settings, key)
            for key in ("football_data_api_key", "thesportsdb_api_key", "balldontlie_api_key")
        ):
            warnings.append(
                "Hiçbir anahtarlı spor kaynağı yapılandırılmadı; "
                "yalnızca F1 ve haberler senkronlanır."
            )
    return errors, warnings


def ensure_valid(settings: Settings) -> list[str]:
    """Raise ConfigurationError listing every problem; return the warnings."""
    errors, warnings = check_settings(settings)
    if errors:
        raise ConfigurationError("Yapılandırma hatası:\n" + "\n".join(f"  - {e}" for e in errors))
    return warnings
