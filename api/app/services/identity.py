"""Cross-provider identity: one club is one row, whichever provider mentions it.

Rule (docs/DECISIONS.md, 2026-11-02):
  1. The provider's own row (source, external_id) or an existing ExternalRef wins.
  2. Otherwise a team of the same sport from ANOTHER source whose normalised name is equal
     (accents, case, punctuation and club affixes such as FC/SK/JK ignored) - and whose country
     matches when both are known - is reused, and an ExternalRef is recorded.
  3. Anything ambiguous (0 or 2+ candidates) creates a new row: a wrong merge is worse than a
     duplicate, and a duplicate can be linked later by adding an ExternalRef.
"""

import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ExternalRef, Team

AFFIXES = {"fc", "afc", "cf", "sk", "jk", "fk", "ac", "as", "sc", "ss", "us", "bk", "if", "kulubu"}
NON_ALNUM = re.compile(r"[^a-z0-9 ]+")


def normalize_name(name: str) -> str:
    """'Beşiktaş JK' -> 'besiktas'; 'İstanbul Başakşehir FK' -> 'istanbul basaksehir'."""
    text = unicodedata.normalize("NFKD", name.replace("İ", "I").replace("ı", "i"))
    text = "".join(c for c in text if not unicodedata.combining(c)).casefold()
    words = [w for w in NON_ALNUM.sub(" ", text).split() if w not in AFFIXES]
    return " ".join(words)


async def linked_team(session: AsyncSession, source: str, external_id: str) -> int | None:
    return await session.scalar(
        select(ExternalRef.entity_id).where(
            ExternalRef.kind == "team",
            ExternalRef.source == source,
            ExternalRef.external_id == external_id,
        )
    )


async def match_team(
    session: AsyncSession, sport_id: int, source: str, name: str, country: str | None
) -> int | None:
    """The single same-sport team of another source with this normalised name, else None."""
    key = normalize_name(name)
    if not key:
        return None
    rows = await session.execute(
        select(Team.id, Team.name, Team.short_name, Team.country).where(
            Team.sport_id == sport_id, Team.source != source
        )
    )
    candidates = {
        team_id
        for team_id, team_name, short, team_country in rows
        if key in {normalize_name(team_name), normalize_name(short or "")}
        and not (country and team_country and country.casefold() != team_country.casefold())
    }
    return next(iter(candidates)) if len(candidates) == 1 else None


async def link_team(session: AsyncSession, team_id: int, source: str, external_id: str) -> None:
    session.add(ExternalRef(kind="team", entity_id=team_id, source=source, external_id=external_id))
    await session.flush()
