from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SourceMeta(BaseModel):
    name: str
    sport: str | None
    configured: bool
    last_success_at: datetime | None = None
    last_attempt_at: datetime | None = None
    last_status: str | None = None


class SportMeta(BaseModel):
    slug: str
    name: str
    configured: bool  # at least one source for this sport is configured
    sources: list[str]


class MetaOut(BaseModel):
    data_mode: Literal["live", "demo"]
    sports: list[SportMeta]
    sources: list[SourceMeta]
