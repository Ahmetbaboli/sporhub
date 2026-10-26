from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ErrorResponse
from app.db.session import get_session
from app.schemas.api import (
    CompetitionDetail,
    EventOut,
    PlayerOut,
    SearchResults,
    TeamDetail,
)
from app.services import read_service as svc

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

NOT_FOUND = {404: {"model": ErrorResponse, "description": "Kayıt bulunamadı"}}

router = APIRouter(prefix="/api/v1", responses=NOT_FOUND)

Session = Annotated[AsyncSession, Depends(get_session)]
PageParam = Annotated[int, Query(ge=1, description="Sayfa numarası")]
PageSizeParam = Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE, description="Sayfa boyutu")]
Order = Annotated[Literal["asc", "desc"], Query(description="start_time sıralaması")]
TimeZoneParam = Annotated[str, Query(description="IANA saat dilimi, ör. Europe/Istanbul")]


def _day_start(value: date | None, end: bool = False) -> datetime | None:
    if value is None:
        return None
    day = value + timedelta(days=1) if end else value
    return datetime.combine(day, time.min, tzinfo=UTC)


@router.get("/sports", response_model=svc.SportList, tags=["sports"])
async def list_sports(session: Session) -> svc.SportList:
    return await svc.get_sports(session)


@router.get(
    "/sports/{sport}/competitions", response_model=svc.CompetitionList, tags=["competitions"]
)
async def list_competitions(sport: str, session: Session) -> svc.CompetitionList:
    return await svc.get_competitions(session, sport)


@router.get(
    "/competitions/{competition}",
    response_model=CompetitionDetail,
    tags=["competitions"],
    summary="Lig detayı (aktif sezon dahil); id veya slug kabul eder",
)
async def get_competition(competition: str, session: Session) -> CompetitionDetail:
    return await svc.get_competition_detail(session, competition)


@router.get(
    "/competitions/{competition}/events", response_model=svc.EventList, tags=["competitions"]
)
async def list_competition_events(
    competition: str,
    session: Session,
    status: Annotated[
        list[Literal["scheduled", "live", "finished", "postponed", "cancelled"]] | None,
        Query(description="Bir veya birden çok durum"),
    ] = None,
    from_: Annotated[
        date | None, Query(alias="from", description="Başlangıç günü (UTC, dahil)")
    ] = None,
    to: Annotated[date | None, Query(description="Bitiş günü (UTC, dahil)")] = None,
    order: Order = "asc",
    page: PageParam = 1,
    page_size: PageSizeParam = DEFAULT_PAGE_SIZE,
) -> svc.EventList:
    return await svc.get_competition_events(
        session,
        competition,
        status=list(status) if status else None,
        start=_day_start(from_),
        end=_day_start(to, end=True),
        descending=order == "desc",
        page=page,
        page_size=page_size,
    )


@router.get(
    "/competitions/{competition}/standings", response_model=svc.StandingList, tags=["competitions"]
)
async def list_standings(competition: str, session: Session) -> svc.StandingList:
    return await svc.get_competition_standings(session, competition)


@router.get("/events/today", response_model=svc.TodayEvents, tags=["events"])
async def today_events(
    session: Session,
    sport: Annotated[str | None, Query(description="Spor slug'ı")] = None,
    day: Annotated[date | None, Query(alias="date", description="Gün; varsayılan bugün")] = None,
    tz: TimeZoneParam = svc.DEFAULT_TZ,
) -> svc.TodayEvents:
    return await svc.get_today_events(session, sport, day, tz)


@router.get("/events/{event_id}", response_model=EventOut, tags=["events"])
async def get_event(event_id: int, session: Session) -> EventOut:
    return await svc.get_event_detail(session, event_id)


@router.get("/teams/{team_id}", response_model=TeamDetail, tags=["teams"])
async def get_team(team_id: int, session: Session) -> TeamDetail:
    return await svc.get_team_detail(session, team_id)


@router.get("/teams/{team_id}/events", response_model=svc.EventList, tags=["teams"])
async def list_team_events(
    team_id: int,
    session: Session,
    order: Order = "desc",
    page: PageParam = 1,
    page_size: PageSizeParam = DEFAULT_PAGE_SIZE,
) -> svc.EventList:
    return await svc.get_team_events(session, team_id, page, page_size, order == "desc")


@router.get("/players/{player_id}", response_model=PlayerOut, tags=["players"])
async def get_player(player_id: int, session: Session) -> PlayerOut:
    return await svc.get_player_detail(session, player_id)


@router.get("/search", response_model=SearchResults, tags=["search"])
async def search(
    session: Session,
    q: Annotated[str, Query(min_length=1, max_length=100, description="Arama metni")],
) -> SearchResults:
    return await svc.search_all(session, q)
