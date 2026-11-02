"""player season stats

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONType = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "player_stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("season_id", sa.Integer(), sa.ForeignKey("seasons.id"), nullable=False),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id")),
        sa.Column("stats", JSONType, nullable=False),
        sa.UniqueConstraint("season_id", "player_id"),
    )
    op.create_index("ix_player_stats_season_id", "player_stats", ["season_id"])
    op.create_index("ix_player_stats_player_id", "player_stats", ["player_id"])


def downgrade() -> None:
    op.drop_index("ix_player_stats_player_id", table_name="player_stats")
    op.drop_index("ix_player_stats_season_id", table_name="player_stats")
    op.drop_table("player_stats")
