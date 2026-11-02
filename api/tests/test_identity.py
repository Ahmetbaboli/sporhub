from types import SimpleNamespace

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.dto import TeamRef
from app.models import ExternalRef, Team
from app.services.identity import normalize_name
from app.services.sync_service import SyncContext, _team_id, _upsert_team, ensure_sport


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Beşiktaş JK", "besiktas"),
        ("İstanbul Başakşehir FK", "istanbul basaksehir"),
        ("Galatasaray SK", "galatasaray"),
        ("Fenerbahçe", "fenerbahce"),
        ("FC Internazionale Milano", "internazionale milano"),
        ("Brighton & Hove Albion FC", "brighton hove albion"),
    ],
)
def test_normalize_name(name: str, expected: str) -> None:
    assert normalize_name(name) == expected


def ctx_for(session: AsyncSession, sport_id: int, source: str) -> SyncContext:
    adapter = SimpleNamespace(record_source=source)
    return SyncContext(session=session, adapter=adapter, sport_id=sport_id)  # type: ignore[arg-type]


async def test_same_club_from_two_providers_is_one_row(
    maker: async_sessionmaker[AsyncSession],
) -> None:
    async with maker() as s:
        sport = await ensure_sport(s, "football", "Futbol")
        tsdb = ctx_for(s, sport, "thesportsdb")
        gs = await _upsert_team(tsdb, TeamRef(external_id="133804", name="Galatasaray"), "Turkey")
        fd = ctx_for(s, sport, "football-data")
        linked = await _upsert_team(fd, TeamRef(external_id="610", name="Galatasaray SK"), "Turkey")
        assert linked == gs
        # Later references by football-data id resolve through the link, without a lookup by name.
        assert await _team_id(ctx_for(s, sport, "football-data"), TeamRef(external_id="610",
                              name="renamed")) == gs  # fmt: skip
        await s.commit()
        assert await s.scalar(select(func.count()).select_from(Team)) == 1
        ref = (await s.scalars(select(ExternalRef))).one()
        assert (ref.kind, ref.entity_id, ref.source, ref.external_id) == (
            "team", gs, "football-data", "610",
        )  # fmt: skip


async def test_country_mismatch_and_ambiguity_create_new_rows(
    maker: async_sessionmaker[AsyncSession],
) -> None:
    async with maker() as s:
        sport = await ensure_sport(s, "football", "Futbol")
        a = ctx_for(s, sport, "a")
        await _upsert_team(a, TeamRef(external_id="1", name="Arsenal FC"), "England")
        await _upsert_team(a, TeamRef(external_id="2", name="Arsenal"), "Ukraine")
        b = ctx_for(s, sport, "b")
        # Two candidates without a country to tell them apart -> no merge.
        ambiguous = await _upsert_team(b, TeamRef(external_id="9", name="Arsenal"), None)
        # Country picks the right one.
        english = await _upsert_team(b, TeamRef(external_id="10", name="Arsenal"), "England")
        await s.commit()
        names = {t.id: (t.source, t.country) for t in (await s.scalars(select(Team))).all()}
        assert names[ambiguous] == ("b", None)
        assert names[english] == ("a", "England")
