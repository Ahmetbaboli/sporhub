"""mark pre-v0.4 rows as demo data

Before v0.4 the seed command always wrote bundled fixtures and sample news under the plain
provider name, so existing rows cannot be trusted as real data. They are re-labelled with the
"demo:" source prefix; live mode then never shows them and `purge_demo` deletes them. Real data
is re-fetched by the next sync. Editor-written news (source "manual") is kept as is.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-02
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("competitions", "teams", "players", "events")
PREFIX = "demo:"


def upgrade() -> None:
    for table in TABLES:
        op.execute(
            f"UPDATE {table} SET source = '{PREFIX}' || source "
            f"WHERE source NOT LIKE '{PREFIX}%'"
        )
    op.execute(
        f"UPDATE news_articles SET source = '{PREFIX}' || source "
        f"WHERE source NOT LIKE '{PREFIX}%' AND source <> 'manual'"
    )


def downgrade() -> None:
    # Irreversible by design: we cannot know which rows were real. Labels stay.
    pass
