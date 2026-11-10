from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UTCDateTime


class User(Base):
    """A signed-in person. Identity comes from the web app's signed token (OAuth provider id)."""

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("provider", "provider_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32))
    provider_id: Mapped[str] = mapped_column(String(128))
    display_name: Mapped[str | None] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    last_seen_at: Mapped[datetime] = mapped_column(UTCDateTime)


class Favorite(Base):
    """One favorited team, player/driver or competition. Exactly one target column is set."""

    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "team_id"),
        UniqueConstraint("user_id", "player_id"),
        UniqueConstraint("user_id", "competition_id"),
        CheckConstraint(
            "(CASE WHEN team_id IS NOT NULL THEN 1 ELSE 0 END)"
            " + (CASE WHEN player_id IS NOT NULL THEN 1 ELSE 0 END)"
            " + (CASE WHEN competition_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_favorites_one_target",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"))
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"))
    competition_id: Mapped[int | None] = mapped_column(
        ForeignKey("competitions.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
