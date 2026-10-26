"""The only place that knows about SQL dialect differences.

Production runs on PostgreSQL; the local test suite may run on SQLite. Everything else in the
codebase must stay dialect-neutral and go through these helpers.
"""

from collections.abc import Callable
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

POSTGRESQL = "postgresql"


def dialect_name(session: AsyncSession) -> str:
    return session.get_bind().dialect.name


def insert_for(session: AsyncSession) -> Callable[[Any], Any]:
    """Return the dialect's `insert()` that supports `.on_conflict_do_update()`."""
    return pg_insert if dialect_name(session) == POSTGRESQL else sqlite_insert
