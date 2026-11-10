"""news articles and tags

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-02
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TZ = sa.DateTime(timezone=True)
CATEGORIES = ("general", "transfer_official", "transfer_rumour", "interview", "tournament")


def upgrade() -> None:
    op.create_table(
        "news_articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(128), nullable=False),
        sa.Column("external_id", sa.String(64), nullable=False),
        sa.Column("sport_id", sa.Integer(), sa.ForeignKey("sports.id")),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("title", sa.String(320), nullable=False),
        sa.Column("summary", sa.String(400), nullable=False),
        sa.Column("image_url", sa.String(1024)),
        sa.Column("author", sa.String(128)),
        sa.Column("published_at", TZ, nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("is_breaking", sa.Boolean(), nullable=False),
        sa.Column("language", sa.String(8), nullable=False),
        sa.UniqueConstraint("source", "external_id"),
        sa.CheckConstraint(f"category IN {CATEGORIES}", name="ck_news_category"),
    )
    op.create_index("ix_news_published", "news_articles", ["published_at"])
    op.create_index("ix_news_articles_sport_id", "news_articles", ["sport_id"])
    op.create_index("ix_news_articles_category", "news_articles", ["category"])
    op.create_table(
        "news_tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "article_id",
            sa.Integer(),
            sa.ForeignKey("news_articles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id", ondelete="CASCADE")),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id", ondelete="CASCADE")),
        sa.Column(
            "competition_id", sa.Integer(), sa.ForeignKey("competitions.id", ondelete="CASCADE")
        ),
        sa.CheckConstraint(
            "(CASE WHEN team_id IS NOT NULL THEN 1 ELSE 0 END)"
            " + (CASE WHEN player_id IS NOT NULL THEN 1 ELSE 0 END)"
            " + (CASE WHEN competition_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_news_tags_one_target",
        ),
    )
    for column in ("article_id", "team_id", "player_id", "competition_id"):
        op.create_index(f"ix_news_tags_{column}", "news_tags", [column])


def downgrade() -> None:
    op.drop_table("news_tags")
    op.drop_table("news_articles")
