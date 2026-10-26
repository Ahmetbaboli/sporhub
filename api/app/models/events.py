from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONType, UTCDateTime
from app.models.catalog import Competition, Player, Team

EVENT_KINDS = ("match", "race", "session")
EVENT_STATUSES = ("scheduled", "live", "finished", "postponed", "cancelled")


class Season(Base):
    __tablename__ = "seasons"
    __table_args__ = (UniqueConstraint("competition_id", "year_label"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id"), index=True)
    year_label: Mapped[str] = mapped_column(String(32))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(default=False)

    competition: Mapped[Competition] = relationship()


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("source", "external_id"),
        CheckConstraint(f"kind IN {EVENT_KINDS}", name="ck_events_kind"),
        CheckConstraint(f"status IN {EVENT_STATUSES}", name="ck_events_status"),
        Index("ix_events_season_start", "season_id", "start_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"))
    external_id: Mapped[str] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(64))
    kind: Mapped[str] = mapped_column(String(16))
    name: Mapped[str | None] = mapped_column(String(255))
    start_time: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    venue: Mapped[str | None] = mapped_column(String(255))
    round: Mapped[str | None] = mapped_column(String(64))
    extra: Mapped[dict] = mapped_column(JSONType, default=dict)

    season: Mapped[Season] = relationship()
    participants: Mapped[list["EventParticipant"]] = relationship(
        back_populates="event", cascade="all, delete-orphan", order_by="EventParticipant.id"
    )


class EventParticipant(Base):
    __tablename__ = "event_participants"
    __table_args__ = (
        CheckConstraint("side IS NULL OR side IN ('home','away')", name="ck_participants_side"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), index=True)
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), index=True)
    side: Mapped[str | None] = mapped_column(String(8))
    score: Mapped[int | None]
    position: Mapped[int | None]
    points: Mapped[float | None]
    extra: Mapped[dict] = mapped_column(JSONType, default=dict)

    event: Mapped[Event] = relationship(back_populates="participants")
    team: Mapped[Team | None] = relationship()
    player: Mapped[Player | None] = relationship()


class Standing(Base):
    __tablename__ = "standings"

    id: Mapped[int] = mapped_column(primary_key=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), index=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    position: Mapped[int]
    played: Mapped[int] = mapped_column(default=0)
    won: Mapped[int] = mapped_column(default=0)
    drawn: Mapped[int] = mapped_column(default=0)
    lost: Mapped[int] = mapped_column(default=0)
    points: Mapped[float] = mapped_column(default=0)
    extra: Mapped[dict] = mapped_column(JSONType, default=dict)

    team: Mapped[Team | None] = relationship()
    player: Mapped[Player | None] = relationship()
