import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.data_mode import is_demo
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.rate_limit import install_rate_limit
from app.core.startup import ConfigurationError, describe_validation_error, ensure_valid
from app.db.dialect import release_scheduler_lock, try_scheduler_lock
from app.db.session import get_engine, get_session, get_sessionmaker
from app.routers import admin, me, news, v1
from app.schemas.api import HealthOut
from app.services.demo_data import has_demo_rows, purge_demo
from app.services.health import health_report
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
    for warning in ensure_valid(settings):
        logger.warning("configuration", extra={"detail": warning})
    async with get_sessionmaker()() as session:
        await ensure_registered_sports(session)
        if not is_demo(settings) and await has_demo_rows(session):
            # Live mode must never show sample data, even if an old database still holds some.
            logger.warning("live mode: removing leftover demo rows")
            await purge_demo(session)
    scheduler, lock = None, None
    if settings.scheduler_enabled:
        # Only the replica holding the lock refreshes data: no double syncs, no double budget.
        lock = await try_scheduler_lock(get_engine())
        if lock is None:
            logger.info("scheduler lock held by another instance; not scheduling here")
        else:
            scheduler = build_scheduler(settings)
            scheduler.start()
            logger.info("scheduler started", extra={"tick_seconds": TICK_SECONDS})
    yield
    if scheduler:
        scheduler.shutdown(wait=False)
    if lock is not None:
        await release_scheduler_lock(lock)


def create_app() -> FastAPI:
    try:
        settings = get_settings()
    except ValidationError as exc:
        raise ConfigurationError(describe_validation_error(exc)) from None
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
    # Added before the access log so it runs inside it: refused requests are logged too.
    install_rate_limit(app)

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

    @app.get(
        "/health",
        response_model=HealthOut,
        tags=["meta"],
        responses={503: {"model": HealthOut, "description": "Veritabanına ulaşılamıyor"}},
    )
    async def health(
        response: Response, session: Annotated[AsyncSession, Depends(get_session)]
    ) -> HealthOut:
        report = await health_report(session, settings)
        if report.status == "down":
            response.status_code = 503
        return report

    app.include_router(v1.router)
    app.include_router(admin.router)
    app.include_router(me.router)
    app.include_router(news.router)
    return app


app = create_app()
