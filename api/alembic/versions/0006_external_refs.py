"""cross-provider identity links

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "external_refs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("external_id", sa.String(64), nullable=False),
        sa.UniqueConstraint("kind", "source", "external_id"),
    )
    op.create_index("ix_external_refs_entity_id", "external_refs", ["entity_id"])


def downgrade() -> None:
    op.drop_table("external_refs")
