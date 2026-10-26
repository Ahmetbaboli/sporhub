"""Verification of the short-lived tokens the web app signs for signed-in users.

The web app (Auth.js) owns the OAuth login; this API owns all user data. After login the web
server mints an HS256 JWT per request with a secret both sides share (API_TOKEN_SECRET):

    iss=justsport-web  aud=justsport-api  sub=<provider>:<provider user id>
    name / picture (optional)  iat  exp  (exp - iat <= 5 minutes)

No second database client exists: the user row is created here on first valid request.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Any

import jwt
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.dialect import insert_for
from app.db.session import get_session
from app.models import User

logger = logging.getLogger(__name__)

ISSUER = "justsport-web"
AUDIENCE = "justsport-api"
ALGORITHM = "HS256"
MAX_TOKEN_LIFETIME_SECONDS = 300
CLOCK_LEEWAY_SECONDS = 5
MIN_SECRET_LENGTH = 32
BEARER_PREFIX = "bearer "


@dataclass(frozen=True)
class TokenClaims:
    provider: str
    provider_id: str
    name: str | None
    picture: str | None


def _unauthorized(message: str = "Geçersiz veya süresi dolmuş oturum belirteci.") -> AppError:
    return AppError(401, "unauthorized", message)


def _secret() -> str:
    secret = get_settings().api_token_secret
    if not secret:
        raise AppError(503, "auth_disabled", "API_TOKEN_SECRET tanımlı değil; hesap uçları kapalı.")
    if len(secret) < MIN_SECRET_LENGTH:
        logger.error("API_TOKEN_SECRET is shorter than %d characters", MIN_SECRET_LENGTH)
        raise AppError(503, "auth_misconfigured", "API_TOKEN_SECRET yeterince uzun değil.")
    return secret


def verify_token(token: str) -> TokenClaims:
    """Validate signature, algorithm, issuer, audience, expiry and maximum lifetime."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            _secret(),
            algorithms=[ALGORITHM],  # pins HS256: "none"/RS256 tokens are rejected
            audience=AUDIENCE,
            issuer=ISSUER,
            leeway=CLOCK_LEEWAY_SECONDS,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
    except jwt.PyJWTError:
        raise _unauthorized() from None
    if payload["exp"] - payload["iat"] > MAX_TOKEN_LIFETIME_SECONDS:
        raise _unauthorized("Belirteç ömrü çok uzun.")
    provider, _, provider_id = str(payload["sub"]).partition(":")
    if not provider or not provider_id:
        raise _unauthorized()
    return TokenClaims(provider, provider_id, payload.get("name"), payload.get("picture"))


async def upsert_user(session: AsyncSession, claims: TokenClaims) -> User:
    now = datetime.now(UTC)
    stmt = insert_for(session)(User).values(
        provider=claims.provider,
        provider_id=claims.provider_id,
        display_name=claims.name,
        avatar_url=claims.picture,
        created_at=now,
        last_seen_at=now,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["provider", "provider_id"],
        set_={
            "display_name": stmt.excluded.display_name,
            "avatar_url": stmt.excluded.avatar_url,
            "last_seen_at": stmt.excluded.last_seen_at,
        },
    )
    await session.execute(stmt)
    await session.commit()
    user = await session.scalar(
        select(User).where(User.provider == claims.provider, User.provider_id == claims.provider_id)
    )
    assert user is not None
    return user


async def current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    authorization: Annotated[
        str | None, Header(description="Bearer <imzalı kısa ömürlü token>")
    ] = None,
) -> User:
    if not authorization or not authorization.lower().startswith(BEARER_PREFIX):
        raise _unauthorized("Kimlik doğrulama gerekli.")
    claims = verify_token(authorization[len(BEARER_PREFIX) :].strip())
    return await upsert_user(session, claims)
