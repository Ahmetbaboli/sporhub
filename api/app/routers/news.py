"""Public news endpoints (headlines + summaries linking to publishers)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ErrorResponse
from app.db.session import get_session
from app.schemas.news import NewsArchive, NewsList, NewsOut
from app.services import news_service
from app.services.news_service import NewsFilters

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 50
MAX_AGE_HOURS = 24 * 30

router = APIRouter(
    prefix="/api/v1/news",
    tags=["news"],
    responses={404: {"model": ErrorResponse, "description": "Kayıt bulunamadı"}},
)

Session = Annotated[AsyncSession, Depends(get_session)]
CategoryParam = Literal[
    "general", "transfer", "transfer_official", "transfer_rumour", "interview", "tournament"
]


def news_filters(
    category: Annotated[
        CategoryParam | None, Query(description="'transfer' = resmî + söylenti")
    ] = None,
    sport: Annotated[str | None, Query(description="Spor slug'ı")] = None,
    team: Annotated[int | None, Query(ge=1)] = None,
    player: Annotated[int | None, Query(ge=1)] = None,
    competition: Annotated[int | None, Query(ge=1)] = None,
    breaking: Annotated[bool | None, Query(description="Yalnızca son dakika")] = None,
    month: Annotated[
        str | None, Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="Arşiv ayı: YYYY-MM")
    ] = None,
    q: Annotated[str | None, Query(min_length=2, max_length=100)] = None,
    language: Annotated[Literal["tr", "en"] | None, Query()] = None,
    max_age_hours: Annotated[
        int | None, Query(ge=1, le=MAX_AGE_HOURS, description="Yalnızca son N saat")
    ] = None,
) -> NewsFilters:
    return NewsFilters(
        category, sport, team, player, competition, breaking, month, q, language, max_age_hours
    )


Filters = Annotated[NewsFilters, Depends(news_filters)]


@router.get("", response_model=NewsList, summary="Haber listesi (filtreli, sayfalı)")
async def list_news(
    session: Session,
    filters: Filters,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> NewsList:
    return await news_service.list_news(session, filters, page, page_size)


@router.get("/archive", response_model=NewsArchive, summary="Aylara göre haber sayıları")
async def archive(session: Session, filters: Filters) -> NewsArchive:
    return await news_service.news_archive(session, filters)


@router.get("/{article_id}", response_model=NewsOut, summary="Tek haber")
async def get_article(article_id: int, session: Session) -> NewsOut:
    return await news_service.get_article(session, article_id)
