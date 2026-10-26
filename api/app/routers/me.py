"""Signed-in user endpoints. Auth: `Authorization: Bearer <token signed by the web app>`."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_user
from app.core.errors import ErrorResponse
from app.db.session import get_session
from app.models import User
from app.schemas.me import Dashboard, FavoriteIds, Favorites, UserOut
from app.services import me_service
from app.services.me_service import FavoriteKind

router = APIRouter(
    prefix="/api/v1/me",
    tags=["me"],
    responses={
        401: {"model": ErrorResponse, "description": "Eksik veya geçersiz token"},
        503: {"model": ErrorResponse, "description": "Hesap uçları yapılandırılmamış"},
    },
)

CurrentUser = Annotated[User, Depends(current_user)]
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=UserOut, summary="Oturumdaki kullanıcı")
async def me(user: CurrentUser) -> User:
    return user


@router.get("/favorites", response_model=Favorites, summary="Favorilerim (ayrıntılı)")
async def favorites(user: CurrentUser, session: Session) -> Favorites:
    return await me_service.list_favorites(session, user.id)


@router.get(
    "/favorites/ids", response_model=FavoriteIds, summary="Favori id'leri (yıldız butonları)"
)
async def favorite_ids(user: CurrentUser, session: Session) -> FavoriteIds:
    return await me_service.favorite_ids(session, user.id)


@router.put(
    "/favorites/{kind}/{entity_id}",
    status_code=204,
    summary="Favoriye ekle (idempotent)",
)
async def add_favorite(
    kind: FavoriteKind, entity_id: int, user: CurrentUser, session: Session
) -> Response:
    await me_service.add_favorite(session, user.id, kind, entity_id)
    return Response(status_code=204)


@router.delete("/favorites/{kind}/{entity_id}", status_code=204, summary="Favoriden çıkar")
async def remove_favorite(
    kind: FavoriteKind, entity_id: int, user: CurrentUser, session: Session
) -> Response:
    await me_service.remove_favorite(session, user.id, kind, entity_id)
    return Response(status_code=204)


@router.get("/dashboard", response_model=Dashboard, summary="Kişisel panel")
async def dashboard(user: CurrentUser, session: Session) -> Dashboard:
    return await me_service.dashboard(session, user.id)
