"""Capture trimmed, real ESPN Süper Lig responses as fixtures (fixtures/espn/).

    PYTHONPATH=. uv run python tools/capture_espn.py

Keeps only the fields the adapter reads, a handful of finished and upcoming matches around
today, the 18 teams and the table. Five requests in total.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from app.adapters.espn_soccer import BASE_URL, USER_AGENT
from app.core.tls import ssl_context

LEAGUE = "tur.1"
OUT = Path(__file__).resolve().parents[1] / "fixtures" / "espn"
EVENTS_EACH_WAY = 6
TIMEOUT_SECONDS = 30


def team(raw: dict[str, Any]) -> dict[str, Any]:
    keep = {
        k: raw[k]
        for k in ("id", "displayName", "abbreviation", "color", "alternateColor")
        if k in raw
    }
    if raw.get("logo"):
        keep["logo"] = raw["logo"]
    if raw.get("logos"):
        keep["logos"] = [{"href": raw["logos"][0]["href"]}]
    return keep


def event(raw: dict[str, Any]) -> dict[str, Any]:
    comp = raw["competitions"][0]
    return {
        "id": raw["id"],
        "date": raw["date"],
        "status": {"type": {k: raw["status"]["type"][k] for k in ("name", "state")}},
        "competitions": [
            {
                "venue": {"fullName": (comp.get("venue") or {}).get("fullName")},
                "competitors": [
                    {
                        "homeAway": c["homeAway"],
                        "score": c.get("score"),
                        "form": c.get("form"),
                        "team": team(c["team"]),
                    }
                    for c in comp["competitors"]
                ],
            }
        ],
    }


def main() -> int:
    now = datetime.now(UTC)
    months = [now.strftime("%Y%m"), f"{now.year}{now.month - 1:02d}" if now.month > 1 else ""]
    with httpx.Client(
        verify=ssl_context(), timeout=TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT}
    ) as client:
        get = lambda path, **params: client.get(BASE_URL + path, params=params).json()  # noqa: E731
        raw = [get(f"/site/v2/sports/soccer/{LEAGUE}/scoreboard", dates=m) for m in months if m]
        teams = get(f"/site/v2/sports/soccer/{LEAGUE}/teams")
        table = get(f"/v2/sports/soccer/{LEAGUE}/standings")
    events = sorted(
        {e["id"]: e for page in raw for e in page["events"]}.values(), key=lambda e: e["date"]
    )
    past = [e for e in events if e["status"]["type"]["state"] == "post"][-EVENTS_EACH_WAY:]
    future = [e for e in events if e["status"]["type"]["state"] == "pre"][:EVENTS_EACH_WAY]
    league = raw[0]["leagues"][0]
    meta = {"reference_date": now.date().isoformat(), "note": "Real ESPN responses, trimmed."}
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        f"scoreboard_{LEAGUE}.json": {
            "_fixture": meta,
            "leagues": [{k: league[k] for k in ("id", "name", "season", "logos") if k in league}],
            "events": [event(e) for e in past + future],
        },
        f"teams_{LEAGUE}.json": {
            "sports": [
                {
                    "leagues": [
                        {
                            "teams": [
                                {"team": team(t["team"])}
                                for t in teams["sports"][0]["leagues"][0]["teams"]
                            ]
                        }
                    ]
                }
            ]
        },
        f"standings_{LEAGUE}.json": {
            "children": [
                {
                    "standings": {
                        "entries": [
                            {
                                "team": team(e["team"]),
                                "note": e.get("note"),
                                "stats": [
                                    {"name": s["name"], "value": s.get("value")} for s in e["stats"]
                                ],
                            }
                            for e in table["children"][0]["standings"]["entries"]
                        ]
                    }
                }
            ]
        },
    }
    for name, data in files.items():
        (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print("wrote", name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
