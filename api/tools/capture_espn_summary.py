"""Capture trimmed, real ESPN match summaries as fixtures (fixtures/espn/summary_<id>.json).

    PYTHONPATH=. uv run python tools/capture_espn_summary.py 401888258 401888256

Keeps only what normalize_match_details reads: lineups, key moments, team stats, attendance.
One request per event, 2 s apart (the adapter's own spacing).
"""

import json
import sys
import time
from pathlib import Path
from typing import Any

import httpx

from app.adapters.espn_soccer import BASE_URL, MIN_REQUEST_INTERVAL_SECONDS, USER_AGENT
from app.core.tls import ssl_context

LEAGUE = "tur.1"
OUT = Path(__file__).resolve().parents[1] / "fixtures" / "espn"
TIMEOUT_SECONDS = 30


def pick(raw: dict[str, Any], *keys: str) -> dict[str, Any]:
    return {k: raw[k] for k in keys if k in raw}


def roster_entry(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        **pick(raw, "starter", "jersey", "subbedIn", "subbedOut", "formationPlace"),
        "athlete": pick(raw.get("athlete") or {}, "id", "displayName"),
        "position": pick(raw.get("position") or {}, "abbreviation"),
    }


def trim(data: dict[str, Any]) -> dict[str, Any]:
    competition = data["header"]["competitions"][0]
    return {
        "header": {
            "competitions": [
                {"competitors": [pick(c, "id", "homeAway") for c in competition["competitors"]]}
            ]
        },
        "boxscore": {
            "teams": [
                {
                    "homeAway": t["homeAway"],
                    "statistics": [
                        pick(s, "name", "displayValue") for s in t.get("statistics") or []
                    ],
                }
                for t in data["boxscore"]["teams"]
            ]
        },
        "rosters": [
            {
                **pick(r, "homeAway", "formation"),
                "roster": [roster_entry(e) for e in r.get("roster") or []],
            }
            for r in data.get("rosters") or []
        ],
        "keyEvents": [
            {
                **pick(e, "scoringPlay"),
                "type": pick(e.get("type") or {}, "type"),
                "clock": pick(e.get("clock") or {}, "displayValue"),
                "team": pick(e.get("team") or {}, "id"),
                "participants": [
                    {"athlete": pick(p.get("athlete") or {}, "displayName")}
                    for p in e.get("participants") or []
                ],
            }
            for e in data.get("keyEvents") or []
        ],
        "gameInfo": pick(data.get("gameInfo") or {}, "attendance"),
    }


def main(event_ids: list[str]) -> int:
    with httpx.Client(
        verify=ssl_context(), timeout=TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT}
    ) as client:
        for i, event_id in enumerate(event_ids):
            if i:
                time.sleep(MIN_REQUEST_INTERVAL_SECONDS)
            response = client.get(
                f"{BASE_URL}/site/v2/sports/soccer/{LEAGUE}/summary", params={"event": event_id}
            )
            response.raise_for_status()
            path = OUT / f"summary_{event_id}.json"
            path.write_text(
                json.dumps(trim(response.json()), ensure_ascii=False, indent=1), encoding="utf-8"
            )
            print("wrote", path.name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
