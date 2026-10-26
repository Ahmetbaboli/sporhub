import httpx
import pytest
import respx

from app.adapters.http import RateLimitedClient
from app.adapters.jolpica import BASE_URL, USER_AGENT, JolpicaAdapter, normalize_race
from app.core.config import Settings


@pytest.fixture
def adapter(settings: Settings) -> JolpicaAdapter:
    return JolpicaAdapter(settings)


def _live(settings: Settings, **update: object) -> JolpicaAdapter:
    adapter = JolpicaAdapter(settings.model_copy(update={"use_fixtures": False, **update}))
    adapter._http = RateLimitedClient(
        BASE_URL, headers={"User-Agent": USER_AGENT}, min_interval=0, backoff_min=0.01
    )
    return adapter


async def test_competition_is_single_f1_season(adapter: JolpicaAdapter) -> None:
    (comp,) = await adapter.fetch_competitions()
    assert (comp.external_id, comp.season_key, comp.season_label) == ("f1", "2026", "2026")
    assert comp.season_start and comp.season_end and comp.season_start < comp.season_end


async def test_calendar_becomes_race_events(adapter: JolpicaAdapter) -> None:
    events = await adapter.fetch_events("f1", "2026")
    assert len(events) == 24
    assert {e.kind for e in events} == {"race"}
    assert [e.round for e in events] == [str(i) for i in range(1, 25)]
    finished = [e for e in events if e.status == "finished"]
    assert len(finished) == 19
    assert all(e.status == "scheduled" and not e.participants for e in events[19:])
    race = finished[0]
    assert race.name == "Australian Grand Prix"
    assert race.venue and "Melbourne" in race.venue
    assert len(race.participants) == 22


async def test_results_are_ordered_and_carry_driver_and_constructor(
    adapter: JolpicaAdapter,
) -> None:
    race = (await adapter.fetch_events("f1", "2026"))[0]
    positions = [p.position for p in race.participants]
    assert positions == sorted(positions)
    winner = race.participants[0]
    assert winner.points == 25 and winner.player_external_id and winner.team
    assert winner.extra["driver"] and winner.extra["grid"] >= 1
    assert sum(p.points or 0 for p in race.participants) == 101  # 25+18+15+12+10+8+6+4+2+1


async def test_standings_contain_both_championships(adapter: JolpicaAdapter) -> None:
    rows = await adapter.fetch_standings("f1", "2026")
    drivers = [r for r in rows if r.extra["kind"] == "driver"]
    teams = [r for r in rows if r.extra["kind"] == "constructor"]
    assert (len(drivers), len(teams)) == (22, 11)
    assert [r.position for r in drivers] == list(range(1, 23))
    assert drivers[0].player_external_id and drivers[0].team is not None
    assert teams[0].player_external_id is None
    assert drivers[0].points >= drivers[1].points
    assert sum(r.points for r in teams) == sum(r.points for r in drivers)


async def test_constructors_carry_their_drivers(adapter: JolpicaAdapter) -> None:
    teams = {t.external_id: t for t in await adapter.fetch_teams("f1", "2026")}
    assert len(teams) == 11
    assert all(len(t.squad) == 2 for t in teams.values())
    assert {p.extra["code"] for p in teams["ferrari"].squad} == {"LEC", "HAM"}


def test_race_without_results_is_scheduled_and_sessions_are_utc() -> None:
    event = normalize_race(
        {
            "season": "2027",
            "round": "1",
            "raceName": "Test GP",
            "date": "2027-03-14",
            "time": "04:00:00Z",
            "Circuit": {
                "circuitId": "x",
                "circuitName": "X Circuit",
                "Location": {"locality": "Town", "country": "Land"},
            },
            "Qualifying": {"date": "2027-03-13", "time": "05:00:00Z"},
        }
    )
    assert event.status == "scheduled"
    assert event.external_id == "2027-1"
    assert event.extra["sessions"]["qualifying"] == "2027-03-13T05:00:00+00:00"


@respx.mock
async def test_live_mode_paginates_and_merges_split_races(settings: Settings) -> None:
    adapter = _live(settings)
    circuit = {"circuitId": "x", "circuitName": "X", "Location": {"locality": "T", "country": "L"}}
    race = {
        "season": "2026",
        "round": "1",
        "raceName": "A GP",
        "date": "2026-03-08",
        "time": "04:00:00Z",
        "Circuit": circuit,
    }

    def result(pos: int) -> dict:
        return {
            "position": str(pos),
            "positionText": str(pos),
            "points": "0",
            "grid": "1",
            "laps": "57",
            "status": "Finished",
            "Driver": {"driverId": f"d{pos}", "givenName": "D", "familyName": str(pos)},
            "Constructor": {"constructorId": "c", "name": "C"},
        }

    def results(request: httpx.Request) -> httpx.Response:
        offset = int(request.url.params["offset"])
        rows = [result(1), result(2)] if offset == 0 else [result(3)]
        return httpx.Response(
            200,
            json={
                "MRData": {
                    "limit": "2",
                    "offset": str(offset),
                    "total": "3",
                    "RaceTable": {"Races": [{**race, "Results": rows}]},
                }
            },
        )

    schedule = respx.get(f"{BASE_URL}/2026/races/").mock(
        return_value=httpx.Response(
            200, json={"MRData": {"limit": "100", "total": "1", "RaceTable": {"Races": [race]}}}
        )
    )
    route = respx.get(f"{BASE_URL}/2026/results/").mock(side_effect=results)
    (event,) = await adapter.fetch_events("f1", "2026")
    assert route.call_count == 2 and schedule.call_count == 1
    assert [p.position for p in event.participants] == [1, 2, 3]
    assert route.calls[0].request.headers["User-Agent"] == USER_AGENT
    assert route.calls[0].request.url.params["limit"] == "100"
    await adapter.aclose()


@respx.mock
async def test_live_mode_never_shifts_dates(settings: Settings) -> None:
    adapter = _live(settings, fixture_today="2030-01-01")
    circuit = {"circuitId": "x", "circuitName": "X", "Location": {"locality": "T", "country": "L"}}
    payload = {
        "_fixture": {"reference_date": "2026-11-01"},
        "MRData": {
            "limit": "100",
            "total": "1",
            "RaceTable": {
                "Races": [
                    {
                        "season": "2026",
                        "round": "1",
                        "raceName": "A GP",
                        "date": "2026-03-08",
                        "time": "04:00:00Z",
                        "Circuit": circuit,
                    }
                ]
            },
        },
    }
    respx.get(f"{BASE_URL}/2026/races/").mock(return_value=httpx.Response(200, json=payload))
    respx.get(f"{BASE_URL}/2026/results/").mock(
        return_value=httpx.Response(
            200, json={"MRData": {"limit": "100", "total": "0", "RaceTable": {"Races": []}}}
        )
    )
    (event,) = await adapter.fetch_events("f1", "2026")
    assert event.start_time.isoformat() == "2026-03-08T04:00:00+00:00"
    await adapter.aclose()
