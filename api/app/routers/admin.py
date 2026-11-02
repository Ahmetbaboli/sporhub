import hashlib
import secrets
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.news_rss import NewsDTO, RssNewsAdapter
from app.adapters.registry import adapter_names, create_adapter
from app.core.config import get_settings
from app.core.errors import AppError, ErrorResponse
from app.core.sources import source_status
from app.db.session import get_session, get_sessionmaker
from app.schemas.api import SyncAccepted
from app.schemas.meta import AdminStatus
from app.schemas.news import ManualNewsCreated, ManualNewsIn
from app.services.meta_service import get_admin_status
from app.services.news_service import MANUAL_SOURCE, create_manual_article, run_news_sync
from app.services.sync_service import run_sync

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    responses={401: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)


def require_admin(token: str | None) -> None:
    expected = get_settings().admin_token
    if not expected:
        raise AppError(503, "admin_disabled", "ADMIN_TOKEN tanımlı değil; admin uçları kapalı.")
    if not token or not secrets.compare_digest(token, expected):
        raise AppError(401, "unauthorized", "Geçersiz admin token.")


NEWS_ADAPTER = "news"


async def _news_sync_in_background() -> None:
    adapter = RssNewsAdapter(get_settings())
    try:
        await run_news_sync(get_sessionmaker(), adapter)
    finally:
        await adapter.aclose()


async def _sync_in_background(name: str) -> None:
    adapter = create_adapter(name, get_settings())
    try:
        await run_sync(get_sessionmaker(), adapter)
    finally:
        await adapter.aclose()


@router.post("/sync/{adapter}", response_model=SyncAccepted, status_code=202)
async def trigger_sync(
    adapter: str,
    background: BackgroundTasks,
    x_admin_token: Annotated[str | None, Header(description="ADMIN_TOKEN değeri")] = None,
) -> SyncAccepted:
    require_admin(x_admin_token)
    if adapter == NEWS_ADAPTER:
        background.add_task(_news_sync_in_background)
        return SyncAccepted(status="accepted", adapter=adapter)
    if adapter not in adapter_names():
        raise AppError(404, "unknown_adapter", f"Bilinmeyen adapter: {adapter}")
    background.add_task(_sync_in_background, adapter)
    return SyncAccepted(status="accepted", adapter=adapter)


@router.post(
    "/news",
    response_model=ManualNewsCreated,
    status_code=201,
    summary="Editörün elle girdiği haber (son dakika duyurusu vb.)",
)
async def create_news(
    body: ManualNewsIn,
    session: Annotated[AsyncSession, Depends(get_session)],
    x_admin_token: Annotated[str | None, Header(description="ADMIN_TOKEN değeri")] = None,
) -> ManualNewsCreated:
    require_admin(x_admin_token)
    url = str(body.url)
    dto = NewsDTO(
        source=MANUAL_SOURCE,
        external_id=hashlib.sha256(url.encode()).hexdigest()[:40],
        url=url,
        title=body.title.strip(),
        summary=body.summary.strip(),
        published_at=body.published_at or datetime.now(UTC),
        category=body.category,
        is_breaking=body.is_breaking,
        language=body.language,
        sport_slug=body.sport,
    )
    return ManualNewsCreated(id=await create_manual_article(session, dto))


class SourceStatusOut(BaseModel):
    name: str
    kind: str
    description: str
    requires_key: bool
    configured: bool


@router.get(
    "/sources",
    response_model=list[SourceStatusOut],
    summary="Veri kaynakları: yapılandırıldı mı (yalnızca evet/hayır, anahtar değeri asla)",
)
async def sources(
    x_admin_token: Annotated[str | None, Header(description="ADMIN_TOKEN değeri")] = None,
) -> list[SourceStatusOut]:
    require_admin(x_admin_token)
    return [SourceStatusOut(**vars(s)) for s in source_status(get_settings())]


@router.get(
    "/status",
    response_model=AdminStatus,
    summary="Senkron durumu: son başarı, 24 saatlik hata oranı, kalan istek bütçesi",
)
async def status(
    session: Annotated[AsyncSession, Depends(get_session)],
    x_admin_token: Annotated[str | None, Header(description="ADMIN_TOKEN değeri")] = None,
) -> AdminStatus:
    require_admin(x_admin_token)
    return await get_admin_status(session, get_settings())
