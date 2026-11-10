"""The only place that knows about SQL dialect differences.

Production runs on PostgreSQL; the local test suite may run on SQLite. Everything else in the
codebase must stay dialect-neutral and go through these helpers.
"""

from collections.abc import Callable
from typing import Any

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession

POSTGRESQL = "postgresql"


def dialect_name(session: AsyncSession) -> str:
    return session.get_bind().dialect.name


def insert_for(session: AsyncSession) -> Callable[[Any], Any]:
    """Return the dialect's `insert()` that supports `.on_conflict_do_update()`."""
    return pg_insert if dialect_name(session) == POSTGRESQL else sqlite_insert


# ---- scheduler lock ---------------------------------------------------------------------------

# Arbitrary, fixed key: every API replica competes for the same PostgreSQL advisory lock.
SCHEDULER_LOCK_KEY = 815_201_026


async def try_scheduler_lock(engine: AsyncEngine) -> AsyncConnection | None:
    """Hold a session-level advisory lock on a dedicated connection for the process lifetime.

    Returns the connection that holds the lock (close it to release), or None when another
    process already holds it. On SQLite (local development only) there is no cross-process
    lock: the single process simply gets an open connection.
    Note: needs a direct (non-pooled) connection; PgBouncer transaction pooling drops
    session locks (docs/DEPLOY.md).
    """
    conn = await engine.connect()
    if engine.dialect.name != POSTGRESQL:
        return conn
    acquired = await conn.scalar(
        text("SELECT pg_try_advisory_lock(:key)"), {"key": SCHEDULER_LOCK_KEY}
    )
    if acquired:
        await conn.commit()  # end the implicit transaction; the session lock stays held
        return conn
    await conn.close()
    return None


async def release_scheduler_lock(conn: AsyncConnection) -> None:
    """Release the lock taken by `try_scheduler_lock` and close its connection.

    Closing alone is not enough: the connection goes back to the pool with its PostgreSQL
    session (and so the session-level lock) still alive.
    """
    if conn.dialect.name == POSTGRESQL:
        await conn.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": SCHEDULER_LOCK_KEY})
        await conn.commit()
    await conn.close()
