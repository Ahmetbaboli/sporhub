from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession


async def upsert_row(
    session: AsyncSession,
    model: type[Any],
    values: dict[str, Any],
    conflict_cols: list[str],
) -> int:
    """INSERT ... ON CONFLICT DO UPDATE on `conflict_cols`; returns the row id.

    Works on PostgreSQL (production) and SQLite (tests).
    """
    insert_fn = pg_insert if session.get_bind().dialect.name == "postgresql" else sqlite_insert
    stmt = insert_fn(model).values(**values)
    updates = {c: stmt.excluded[c] for c in values if c not in conflict_cols}
    stmt = stmt.on_conflict_do_update(index_elements=conflict_cols, set_=updates)
    result = await session.execute(stmt.returning(model.id))
    return result.scalar_one()
