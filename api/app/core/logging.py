import json
import logging
import sys
from datetime import UTC, datetime

# Fields that must never reach the logs, even if a caller passes them as `extra`.
SENSITIVE_KEYS = frozenset({"authorization", "x-auth-token", "x-admin-token", "token", "api_key"})
_RESERVED = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in _RESERVED:
                continue
            payload[key] = "***" if key.lower() in SENSITIVE_KEYS else value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        line = json.dumps(payload, default=str, ensure_ascii=False)
        try:
            from app.core.redact import redact  # late import: settings may not be ready yet

            return redact(line)
        except Exception:  # never lose a log line because settings failed to load
            return line


def configure_logging(level: str = "info") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())
    # httpx logs full URLs at INFO; keep it quiet so tokens in URLs can never leak.
    logging.getLogger("httpx").setLevel(logging.WARNING)
