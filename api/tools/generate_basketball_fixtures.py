"""Generates deterministic sample fixtures in the raw balldontlie (NBA v1) JSON format.

Teams are the real 30 NBA franchises; players and scores are synthetic.
Run:  uv run python tools/generate_basketball_fixtures.py
"""

import json
import random
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "fixtures" / "balldontlie"
SEASON = 2026
REFERENCE_DATE = date(2026, 10, 26)
# The sample "now": games tipped within GAME_LENGTH before it are live, earlier ones are final.
SAMPLE_NOW = datetime(2026, 10, 26, 3, 30, tzinfo=UTC)
GAME_LENGTH = timedelta(hours=2, minutes=30)
DAYS_BEFORE = 6
DAYS_AFTER = 7
POSITIONS = ["G", "G", "G-F", "F", "F", "F-C", "C", "G", "F", "F", "C", "G", "F"]
FIRST = [
    "Jalen",
    "Marcus",
    "Devin",
    "Tyrese",
    "Malik",
    "Isaiah",
    "Cade",
    "Jaylen",
    "Aaron",
    "Luka",
    "Nikola",
    "Zion",
    "Trae",
    "Bam",
    "Jamal",
    "Franz",
    "Paolo",
    "Evan",
    "Walker",
    "Dyson",
]
LAST = [
    "Williams",
    "Johnson",
    "Brooks",
    "Harris",
    "Carter",
    "Mitchell",
    "Thompson",
    "Davis",
    "Robinson",
    "Wright",
    "Bryant",
    "Coleman",
    "Foster",
    "Grant",
    "Hayes",
    "Jordan",
    "Knight",
    "Lawson",
    "Morris",
    "Nash",
    "Owens",
    "Powell",
    "Reed",
    "Sims",
    "Tate",
    "Young",
]
COUNTRIES = ["USA"] * 8 + ["Canada", "France", "Serbia", "Germany", "Australia", "Slovenia"]

# (id, abbreviation, city, name, conference, division)
TEAMS = [
    (1, "ATL", "Atlanta", "Hawks", "East", "Southeast"),
    (2, "BOS", "Boston", "Celtics", "East", "Atlantic"),
    (3, "BKN", "Brooklyn", "Nets", "East", "Atlantic"),
    (4, "CHA", "Charlotte", "Hornets", "East", "Southeast"),
    (5, "CHI", "Chicago", "Bulls", "East", "Central"),
    (6, "CLE", "Cleveland", "Cavaliers", "East", "Central"),
    (7, "DAL", "Dallas", "Mavericks", "West", "Southwest"),
    (8, "DEN", "Denver", "Nuggets", "West", "Northwest"),
    (9, "DET", "Detroit", "Pistons", "East", "Central"),
    (10, "GSW", "Golden State", "Warriors", "West", "Pacific"),
    (11, "HOU", "Houston", "Rockets", "West", "Southwest"),
    (12, "IND", "Indiana", "Pacers", "East", "Central"),
    (13, "LAC", "LA", "Clippers", "West", "Pacific"),
    (14, "LAL", "Los Angeles", "Lakers", "West", "Pacific"),
    (15, "MEM", "Memphis", "Grizzlies", "West", "Southwest"),
    (16, "MIA", "Miami", "Heat", "East", "Southeast"),
    (17, "MIL", "Milwaukee", "Bucks", "East", "Central"),
    (18, "MIN", "Minnesota", "Timberwolves", "West", "Northwest"),
    (19, "NOP", "New Orleans", "Pelicans", "West", "Southwest"),
    (20, "NYK", "New York", "Knicks", "East", "Atlantic"),
    (21, "OKC", "Oklahoma City", "Thunder", "West", "Northwest"),
    (22, "ORL", "Orlando", "Magic", "East", "Southeast"),
    (23, "PHI", "Philadelphia", "76ers", "East", "Atlantic"),
    (24, "PHX", "Phoenix", "Suns", "West", "Pacific"),
    (25, "POR", "Portland", "Trail Blazers", "West", "Northwest"),
    (26, "SAC", "Sacramento", "Kings", "West", "Pacific"),
    (27, "SAS", "San Antonio", "Spurs", "West", "Southwest"),
    (28, "TOR", "Toronto", "Raptors", "East", "Atlantic"),
    (29, "UTA", "Utah", "Jazz", "West", "Northwest"),
    (30, "WAS", "Washington", "Wizards", "East", "Southeast"),
]
META = {
    "reference_date": REFERENCE_DATE.isoformat(),
    "note": "Synthetic sample data in balldontlie NBA v1 format.",
}


def team_json(t: tuple) -> dict:
    return {
        "id": t[0],
        "conference": t[4],
        "division": t[5],
        "city": t[2],
        "name": t[3],
        "full_name": f"{t[2]} {t[3]}",
        "abbreviation": t[1],
    }


def player_json(rng: random.Random, team: tuple, index: int) -> dict:
    feet = rng.choice([(6, 2), (6, 4), (6, 6), (6, 8), (6, 9), (6, 11), (7, 0)])
    return {
        "id": team[0] * 100 + index,
        "first_name": rng.choice(FIRST),
        "last_name": rng.choice(LAST),
        "position": POSITIONS[index % len(POSITIONS)],
        "height": f"{feet[0]}-{feet[1]}",
        "weight": str(rng.randint(180, 260)),
        "jersey_number": str(rng.randint(0, 45)),
        "college": None,
        "country": rng.choice(COUNTRIES),
        "draft_year": rng.randint(2012, 2025),
        "draft_round": 1,
        "draft_number": rng.randint(1, 60),
        "team": team_json(team),
    }


def game_json(
    gid: int, day: date, tip_utc: datetime, home: tuple, away: tuple, rng: random.Random
) -> dict:
    elapsed = SAMPLE_NOW - tip_utc
    kind = (
        "scheduled"
        if elapsed < timedelta(0)
        else "final"
        if elapsed >= GAME_LENGTH
        else "in_progress"
    )
    live = kind == "in_progress"
    hs = max(80, round(rng.gauss(113, 11)))
    vs = max(80, round(rng.gauss(111, 11)))
    if hs == vs:
        hs += 1
    played = kind in ("final", "in_progress")
    if live:
        hs, vs = rng.randint(55, 78), rng.randint(55, 78)
    status = {
        "final": "Final",
        "in_progress": "3rd Qtr",
        "scheduled": tip_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }[kind]
    return {
        "id": gid,
        "date": day.isoformat(),
        "datetime": tip_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "season": SEASON,
        "postseason": False,
        "postponed": False,
        "status": status,
        "status_state": kind,
        "period": 3 if live else (4 if kind == "final" else 0),
        "time": "5:12" if live else ("" if kind == "final" else None),
        "home_team_score": hs if played else 0,
        "visitor_team_score": vs if played else 0,
        "home_team": team_json(home),
        "visitor_team": team_json(away),
    }


def write(name: str, data: list[dict], per_page: int = 100) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {"_fixture": META, "data": data, "meta": {"per_page": per_page, "next_cursor": None}}
    (OUT / f"{name}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )


def main() -> None:
    rng = random.Random(SEASON)
    teams = list(TEAMS)
    write("teams", [team_json(t) for t in teams])
    write("players_active", [player_json(rng, t, i) for t in teams for i in range(len(POSITIONS))])

    games, gid = [], 15_000_000
    for offset in range(-DAYS_BEFORE, DAYS_AFTER + 1):
        day = REFERENCE_DATE + timedelta(days=offset)
        pool = teams[:]
        rng.shuffle(pool)
        for n in range(rng.randint(5, 11)):
            home, away = pool[2 * n], pool[2 * n + 1]
            hour = rng.choice([0, 0, 1, 2, 3])  # 7-10 pm ET, i.e. UTC of the next day
            tip = datetime(day.year, day.month, day.day, tzinfo=UTC) + timedelta(
                days=1 if hour < 4 else 0, hours=hour
            )
            games.append(game_json(gid, day, tip, home, away, rng))
            gid += 1
    write("games_regular", games)
    write("games_playoffs", [])


if __name__ == "__main__":
    main()
