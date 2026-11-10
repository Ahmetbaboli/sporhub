"""users and favorites

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-27
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_id", sa.String(128), nullable=False),
        sa.Column("display_name", sa.String(255)),
        sa.Column("avatar_url", sa.String(512)),
        sa.Column("created_at", TZ, nullable=False),
        sa.Column("last_seen_at", TZ, nullable=False),
        sa.UniqueConstraint("provider", "provider_id"),
    )
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id", ondelete="CASCADE")),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id", ondelete="CASCADE")),
        sa.Column(
            "competition_id", sa.Integer(), sa.ForeignKey("competitions.id", ondelete="CASCADE")
        ),
        sa.Column("created_at", TZ, nullable=False),
        sa.UniqueConstraint("user_id", "team_id"),
        sa.UniqueConstraint("user_id", "player_id"),
        sa.UniqueConstraint("user_id", "competition_id"),
        sa.CheckConstraint(
            "(CASE WHEN team_id IS NOT NULL THEN 1 ELSE 0 END)"
            " + (CASE WHEN player_id IS NOT NULL THEN 1 ELSE 0 END)"
            " + (CASE WHEN competition_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_favorites_one_target",
        ),
    )
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"])


def downgrade() -> None:
    op.drop_table("favorites")
    op.drop_table("users")
