"""Derive synthetic football-data `scorers` fixtures from the existing sample matches/squads.

Each team's real fixture goal total (finished matches) is shared among its players, weighted by
position, so a club's scorers never exceed the goals it actually scored in the sample data.
Deterministic (seeded): re-running produces identical files.

    PYTHONPATH=. uv run python tools/generate_scorers.py
"""

import json
import random
from collections import Counter
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "football_data"
CODES = ("PL", "PD", "SA", "BL1", "CL")
SEED = 20261102
TOP_N = 50
POSITION_WEIGHT = {"Offence": 6.0, "Midfield": 2.5, "Defence": 0.6, "Goalkeeper": 0.0}
ASSIST_RATIO = 0.7
PENALTY_SHARE = 0.12
MIN_APPEARANCE_SHARE = 0.6


def load(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def team_totals(matches: list[dict]) -> tuple[Counter, Counter]:
    goals, played = Counter(), Counter()
    for m in matches:
        if m["status"] != "FINISHED":
            continue
        full = m["score"]["fullTime"]
        for side, key in (("homeTeam", "home"), ("awayTeam", "away")):
            goals[m[side]["id"]] += full[key] or 0
            played[m[side]["id"]] += 1
    return goals, played


def share(rng: random.Random, total: int, weights: list[float]) -> list[int]:
    counts = [0] * len(weights)
    if total <= 0 or sum(weights) == 0:
        return counts
    for _ in range(total):
        counts[rng.choices(range(len(weights)), weights=weights)[0]] += 1
    return counts


def scorers_for(code: str, rng: random.Random) -> dict:
    teams = load(f"{code}_teams")
    matches = load(f"{code}_matches")["matches"]
    goals, played = team_totals(matches)
    rows = []
    for team in teams["teams"]:
        squad = team.get("squad", [])
        weights = [
            POSITION_WEIGHT.get(p.get("position"), 1.0) * rng.uniform(0.3, 1.7) for p in squad
        ]
        team_goals = share(rng, goals[team["id"]], weights)
        team_assists = share(rng, round(goals[team["id"]] * ASSIST_RATIO), [w + 1 for w in weights])
        ref = {k: team[k] for k in ("id", "name", "shortName", "tla", "crest")}
        for player, g, a in zip(squad, team_goals, team_assists, strict=True):
            if g == 0:
                continue
            games = played[team["id"]]
            rows.append(
                {
                    "player": {**player, "section": player.get("position")},
                    "team": ref,
                    "playedMatches": rng.randint(
                        max(1, round(games * MIN_APPEARANCE_SHARE)), games
                    ),
                    "goals": g,
                    "assists": a,
                    "penalties": sum(rng.random() < PENALTY_SHARE for _ in range(g)),
                }
            )
    rows.sort(key=lambda r: (-r["goals"], -r["assists"], r["player"]["name"]))
    return {
        "_fixture": {"note": "Synthetic scorers derived from the sample matches."},
        "count": min(len(rows), TOP_N),
        "scorers": rows[:TOP_N],
    }


def main() -> None:
    rng = random.Random(SEED)
    for code in CODES:
        payload = scorers_for(code, rng)
        path = FIXTURES / f"{code}_scorers.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{path.name}: {payload['count']} scorers")


if __name__ == "__main__":
    main()
