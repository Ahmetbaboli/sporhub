"""merged duplicate news: other sources of the same story

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONType = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    with op.batch_alter_table("news_articles") as batch:
        batch.add_column(sa.Column("also_sources", JSONType, nullable=False, server_default="[]"))


def downgrade() -> None:
    with op.batch_alter_table("news_articles") as batch:
        batch.drop_column("also_sources")
