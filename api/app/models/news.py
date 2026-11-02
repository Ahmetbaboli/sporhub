from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONType, UTCDateTime
from app.models.catalog import Competition, Player, Sport, Team

NEWS_CATEGORIES = ("general", "transfer_official", "transfer_rumour", "interview", "tournament")


class NewsArticle(Base):
    """A headline + short summary linking to the publisher (we never store full articles)."""

    __tablename__ = "news_articles"
    __table_args__ = (
        UniqueConstraint("source", "external_id"),
        CheckConstraint(f"category IN {NEWS_CATEGORIES}", name="ck_news_category"),
        Index("ix_news_published", "published_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(128))
    external_id: Mapped[str] = mapped_column(String(64))
    sport_id: Mapped[int | None] = mapped_column(ForeignKey("sports.id"), index=True)
    url: Mapped[str] = mapped_column(String(1024))
    title: Mapped[str] = mapped_column(String(320))
    summary: Mapped[str] = mapped_column(String(400), default="")
    image_url: Mapped[str | None] = mapped_column(String(1024))
    author: Mapped[str | None] = mapped_column(String(128))
    published_at: Mapped[datetime] = mapped_column(UTCDateTime)
    category: Mapped[str] = mapped_column(String(32), index=True)
    is_breaking: Mapped[bool] = mapped_column(Boolean, default=False)
    language: Mapped[str] = mapped_column(String(8), default="tr")
    # Other publishers that ran the same story: [{"source": ..., "url": ...}] (merged copies).
    also_sources: Mapped[list] = mapped_column(JSONType, default=list)

    sport: Mapped[Sport | None] = relationship()
    tags: Mapped[list["NewsTag"]] = relationship(
        back_populates="article", cascade="all, delete-orphan", order_by="NewsTag.id"
    )


class NewsTag(Base):
    """Links an article to a team, player or competition it mentions (exactly one set)."""

    __tablename__ = "news_tags"
    __table_args__ = (
        CheckConstraint(
            "(team_id IS NOT NULL) + (player_id IS NOT NULL) + (competition_id IS NOT NULL) = 1",
            name="ck_news_tags_one_target",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("news_articles.id", ondelete="CASCADE"), index=True
    )
    team_id: Mapped[int | None] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), index=True
    )
    player_id: Mapped[int | None] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), index=True
    )
    competition_id: Mapped[int | None] = mapped_column(
        ForeignKey("competitions.id", ondelete="CASCADE"), index=True
    )

    article: Mapped[NewsArticle] = relationship(back_populates="tags")
    team: Mapped[Team | None] = relationship()
    player: Mapped[Player | None] = relationship()
    competition: Mapped[Competition | None] = relationship()
