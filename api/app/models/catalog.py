from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONType


class Sport(Base):
    __tablename__ = "sports"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(128))


class Competition(Base):
    __tablename__ = "competitions"
    __table_args__ = (
        UniqueConstraint("source", "external_id"),
        UniqueConstraint("sport_id", "slug"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(64))
    slug: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(128))
    logo_url: Mapped[str | None] = mapped_column(String(512))

    sport: Mapped[Sport] = relationship()


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("source", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255), index=True)
    short_name: Mapped[str | None] = mapped_column(String(64))
    logo_url: Mapped[str | None] = mapped_column(String(512))
    country: Mapped[str | None] = mapped_column(String(128))

    sport: Mapped[Sport] = relationship()


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (UniqueConstraint("source", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255), index=True)
    position: Mapped[str | None] = mapped_column(String(64))
    nationality: Mapped[str | None] = mapped_column(String(128))
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), index=True)
    extra: Mapped[dict] = mapped_column(JSONType, default=dict)

    sport: Mapped[Sport] = relationship()
    team: Mapped[Team | None] = relationship()
