import secrets
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Header

from app.adapters.registry import adapter_names, create_adapter
from app.core.config import get_settings
from app.core.errors import AppError, ErrorResponse
from app.db.session import get_sessionmaker
from app.schemas.api import SyncAccepted
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
    if adapter not in adapter_names():
        raise AppError(404, "unknown_adapter", f"Bilinmeyen adapter: {adapter}")
    background.add_task(_sync_in_background, adapter)
    return SyncAccepted(status="accepted", adapter=adapter)
