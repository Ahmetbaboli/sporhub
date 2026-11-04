"""team colours from the provider (ESPN team.color / alternateColor)

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-04
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

HEX_COLOR_LENGTH = 7  # "#RRGGBB"


def upgrade() -> None:
    with op.batch_alter_table("teams") as batch:
        batch.add_column(sa.Column("color", sa.String(HEX_COLOR_LENGTH), nullable=True))
        batch.add_column(sa.Column("alternate_color", sa.String(HEX_COLOR_LENGTH), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("teams") as batch:
        batch.drop_column("alternate_color")
        batch.drop_column("color")
