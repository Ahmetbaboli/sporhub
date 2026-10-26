"""Capture REAL Jolpica-F1 responses and turn them into anonymized fixtures.

Anonymization: Wikipedia `url` fields and drivers' dates of birth are dropped; only what the
adapter reads is kept. Pages are merged into one file per endpoint (limit == total) and stamped
with `_fixture.reference_date` = the capture day, so fixture mode re-anchors them to "today".

Respects the documented limits (4 req/s burst, 500 req/h): ~10 requests, 0.3 s apart.

Run:  PYTHONPATH=. uv run python tools/capture_jolpica.py 2026
"""

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from app.adapters.jolpica import BASE_URL, PAGE_LIMIT, USER_AGENT

OUT = Path(__file__).resolve().parents[1] / "fixtures" / "jolpica"
REQUEST_SPACING_SECONDS = 0.3
DROP_KEYS = {"url", "dateOfBirth"}


def scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items() if k not in DROP_KEYS}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value


class Capture:
    def __init__(self) -> None:
        self.client = httpx.Client(
            base_url=BASE_URL, headers={"User-Agent": USER_AGENT}, timeout=20
        )
        self.requests = 0

    def get(self, path: str, offset: int = 0) -> dict[str, Any]:
        time.sleep(REQUEST_SPACING_SECONDS)
        self.requests += 1
        response = self.client.get(path, params={"limit": PAGE_LIMIT, "offset": offset})
        response.raise_for_status()
        return response.json()["MRData"]

    def pages(self, path: str, table: str, key: str) -> tuple[list[dict], int]:
        rows: list[dict] = []
        offset = 0
        while True:
            mr = self.get(path, offset)
            rows.extend(mr[table][key])
            offset += int(mr["limit"])
            if offset >= int(mr["total"]):
                return rows, int(mr["total"])


def write(name: str, mr: dict[str, Any]) -> None:
    payload = {
        "_fixture": {
            "reference_date": datetime.now(UTC).date().isoformat(),
            "note": "Anonymized capture of real Jolpica-F1 responses (urls and birth dates removed).",
        },
        "MRData": scrub(mr),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=1) + "\n"
    (OUT / f"{name}.json").write_text(text, encoding="utf-8", newline="\n")


def shell(total: int, **tables: Any) -> dict[str, Any]:
    return {"series": "f1", "limit": str(total), "offset": "0", "total": str(total), **tables}


def merge_results(parts: list[dict]) -> list[dict]:
    """A page boundary can split a race: merge result rows by round."""
    races: dict[str, dict] = {}
    for part in parts:
        race = races.setdefault(part["round"], {**part, "Results": []})
        race["Results"].extend(part.get("Results", []))
    return list(races.values())


def main(season: str) -> None:
    cap = Capture()
    races, total = cap.pages(f"/{season}/races/", "RaceTable", "Races")
    write(f"{season}_races", shell(total, RaceTable={"season": season, "Races": races}))

    parts, _ = cap.pages(f"/{season}/results/", "RaceTable", "Races")
    results = merge_results(parts)
    rows = sum(len(r["Results"]) for r in results)
    write(f"{season}_results", shell(rows, RaceTable={"season": season, "Races": results}))

    constructors, total = cap.pages(f"/{season}/constructors/", "ConstructorTable", "Constructors")
    write(
        f"{season}_constructors",
        shell(total, ConstructorTable={"season": season, "Constructors": constructors}),
    )

    for name, key in (
        ("driverstandings", "DriverStandings"),
        ("constructorstandings", "ConstructorStandings"),
    ):
        mr = cap.get(f"/{season}/{name}/")
        write(f"{season}_{name}", shell(int(mr["total"]), StandingsTable=mr["StandingsTable"]))
        print(name, len(mr["StandingsTable"]["StandingsLists"][0][key]))
    print(f"captured {season}: {len(races)} races, {rows} result rows, {cap.requests} requests")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(datetime.now(UTC).year))
