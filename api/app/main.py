import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.data_mode import is_demo
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.db.session import get_sessionmaker
from app.routers import admin, me, news, v1
from app.schemas.api import HealthOut
from app.services.demo_data import has_demo_rows, purge_demo
from app.services.meta_service import ensure_registered_sports
from app.services.scheduler import TICK_SECONDS, build_scheduler

logger = logging.getLogger(__name__)

DESCRIPTION = """
Just Sport — çok sporlu veri API'si. Veriler dış kaynaklardan senkronize edilir ve ortak
şemada sunulur. Hata gövdesi her zaman `{"error": {"code", "message"}}` biçimindedir.
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    async with get_sessionmaker()() as session:
        await ensure_registered_sports(session)
        if not is_demo(settings) and await has_demo_rows(session):
            # Live mode must never show sample data, even if an old database still holds some.
            logger.warning("live mode: removing leftover demo rows")
            await purge_demo(session)
    scheduler = build_scheduler(settings) if settings.scheduler_enabled else None
    if scheduler:
        scheduler.start()
        logger.info("scheduler started", extra={"tick_seconds": TICK_SECONDS})
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=DESCRIPTION,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    register_error_handlers(app)

    @app.middleware("http")
    async def access_log(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "ms": round((time.perf_counter() - started) * 1000, 1),
            },
        )
        return response

    @app.get("/health", response_model=HealthOut, tags=["meta"])
    async def health() -> HealthOut:
        return HealthOut(status="ok", version=settings.app_version)

    app.include_router(v1.router)
    app.include_router(admin.router)
    app.include_router(me.router)
    app.include_router(news.router)
    return app


app = create_app()
