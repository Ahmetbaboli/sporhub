#!/bin/sh
set -e
alembic upgrade head
# Sample data only ever goes into a demo database.
if [ "${SEED_ON_START:-false}" = "true" ] && [ "${DATA_MODE:-live}" = "demo" ]; then
  python -m app.scripts.seed
fi
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
