"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-26
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSONType = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")
TZ = sa.DateTime(timezone=True)

SPORTS = [
    {"slug": "football", "name": "Futbol"},
    {"slug": "basketball", "name": "Basketbol"},
    {"slug": "formula-1", "name": "Formula 1"},
]


def pk() -> sa.Column:
    return sa.Column("id", sa.Integer(), primary_key=True)


def upgrade() -> None:
    sports = op.create_table(
        "sports",
        pk(),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
    )
    op.bulk_insert(sports, SPORTS)

    op.create_table(
        "competitions",
        pk(),
        sa.Column("sport_id", sa.Integer(), sa.ForeignKey("sports.id"), nullable=False),
        sa.Column("external_id", sa.String(64), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("country", sa.String(128)),
        sa.Column("logo_url", sa.String(512)),
        sa.UniqueConstraint("source", "external_id"),
        sa.UniqueConstraint("sport_id", "slug"),
    )
    op.create_index("ix_competitions_sport_id", "competitions", ["sport_id"])

    op.create_table(
        "teams",
        pk(),
        sa.Column("sport_id", sa.Integer(), sa.ForeignKey("sports.id"), nullable=False),
        sa.Column("external_id", sa.String(64), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("short_name", sa.String(64)),
        sa.Column("logo_url", sa.String(512)),
        sa.Column("country", sa.String(128)),
        sa.UniqueConstraint("source", "external_id"),
    )
    op.create_index("ix_teams_sport_id", "teams", ["sport_id"])
    op.create_index("ix_teams_name", "teams", ["name"])

    op.create_table(
        "players",
        pk(),
        sa.Column("sport_id", sa.Integer(), sa.ForeignKey("sports.id"), nullable=False),
        sa.Column("external_id", sa.String(64), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("position", sa.String(64)),
        sa.Column("nationality", sa.String(128)),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id")),
        sa.Column("extra", JSONType, nullable=False),
        sa.UniqueConstraint("source", "external_id"),
    )
    op.create_index("ix_players_sport_id", "players", ["sport_id"])
    op.create_index("ix_players_name", "players", ["name"])
    op.create_index("ix_players_team_id", "players", ["team_id"])

    op.create_table(
        "seasons",
        pk(),
        sa.Column("competition_id", sa.Integer(), sa.ForeignKey("competitions.id"), nullable=False),
        sa.Column("year_label", sa.String(32), nullable=False),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("competition_id", "year_label"),
    )
    op.create_index("ix_seasons_competition_id", "seasons", ["competition_id"])

    op.create_table(
        "events",
        pk(),
        sa.Column("season_id", sa.Integer(), sa.ForeignKey("seasons.id"), nullable=False),
        sa.Column("external_id", sa.String(64), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("start_time", TZ, nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("venue", sa.String(255)),
        sa.Column("round", sa.String(64)),
        sa.Column("extra", JSONType, nullable=False),
        sa.UniqueConstraint("source", "external_id"),
        sa.CheckConstraint("kind IN ('match', 'race', 'session')", name="ck_events_kind"),
        sa.CheckConstraint(
            "status IN ('scheduled', 'live', 'finished', 'postponed', 'cancelled')",
            name="ck_events_status",
        ),
    )
    op.create_index("ix_events_start_time", "events", ["start_time"])
    op.create_index("ix_events_status", "events", ["status"])
    op.create_index("ix_events_season_start", "events", ["season_id", "start_time"])

    op.create_table(
        "event_participants",
        pk(),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id")),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id")),
        sa.Column("side", sa.String(8)),
        sa.Column("score", sa.Integer()),
        sa.Column("position", sa.Integer()),
        sa.Column("points", sa.Float()),
        sa.Column("extra", JSONType, nullable=False),
        sa.CheckConstraint("side IS NULL OR side IN ('home','away')", name="ck_participants_side"),
    )
    op.create_index("ix_event_participants_event_id", "event_participants", ["event_id"])
    op.create_index("ix_event_participants_team_id", "event_participants", ["team_id"])
    op.create_index("ix_event_participants_player_id", "event_participants", ["player_id"])

    op.create_table(
        "standings",
        pk(),
        sa.Column("season_id", sa.Integer(), sa.ForeignKey("seasons.id"), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id")),
        sa.Column("player_id", sa.Integer(), sa.ForeignKey("players.id")),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("played", sa.Integer(), nullable=False),
        sa.Column("won", sa.Integer(), nullable=False),
        sa.Column("drawn", sa.Integer(), nullable=False),
        sa.Column("lost", sa.Integer(), nullable=False),
        sa.Column("points", sa.Float(), nullable=False),
        sa.Column("extra", JSONType, nullable=False),
    )
    op.create_index("ix_standings_season_id", "standings", ["season_id"])

    op.create_table(
        "sync_runs",
        pk(),
        sa.Column("adapter", sa.String(64), nullable=False),
        sa.Column("started_at", TZ, nullable=False),
        sa.Column("finished_at", TZ),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("items_upserted", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text()),
    )
    op.create_index("ix_sync_runs_adapter", "sync_runs", ["adapter"])


def downgrade() -> None:
    for table in (
        "sync_runs",
        "standings",
        "event_participants",
        "events",
        "seasons",
        "players",
        "teams",
        "competitions",
        "sports",
    ):
        op.drop_table(table)
