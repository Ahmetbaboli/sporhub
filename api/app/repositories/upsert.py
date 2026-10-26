from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dialect import insert_for


async def upsert_row(
    session: AsyncSession,
    model: type[Any],
    values: dict[str, Any],
    conflict_cols: list[str],
) -> int:
    """INSERT ... ON CONFLICT DO UPDATE on `conflict_cols`; returns the row id."""
    stmt = insert_for(session)(model).values(**values)
    updates = {c: stmt.excluded[c] for c in values if c not in conflict_cols}
    stmt = stmt.on_conflict_do_update(index_elements=conflict_cols, set_=updates)
    result = await session.execute(stmt.returning(model.id))
    return result.scalar_one()
