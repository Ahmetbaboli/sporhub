"""Generates deterministic sample fixtures in the raw football-data.org v4 format.

Team names are real; squads and results are synthetic sample data.
Run:  uv run python tools/generate_fixtures.py
"""

import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "fixtures" / "football_data"
REFERENCE_DATE = datetime(2026, 10, 26, 12, 0, tzinfo=UTC)
SEASON_START = "2026-08-15"
SEASON_END = "2027-05-30"
PLAYED_ROUNDS = 9
TOTAL_ROUNDS = 12
SQUAD_POSITIONS = (
    ["Goalkeeper"] * 2
    + ["Centre-Back"] * 3
    + ["Left-Back", "Right-Back"]
    + ["Central Midfield"] * 3
    + ["Attacking Midfield"]
    + ["Left Winger", "Right Winger"]
    + ["Centre-Forward"] * 2
)

FIRST = [
    "Luca",
    "Mateo",
    "Jonas",
    "Arda",
    "Emre",
    "Diego",
    "Noah",
    "Hugo",
    "Ivan",
    "Karim",
    "Leo",
    "Marco",
    "Nico",
    "Omar",
    "Pedro",
    "Rafael",
    "Sami",
    "Tomas",
    "Viktor",
    "Yusuf",
]
LAST = [
    "Almeida",
    "Brandt",
    "Costa",
    "Demir",
    "Eriksen",
    "Fofana",
    "Garcia",
    "Hoffmann",
    "Ilic",
    "Jansen",
    "Kaya",
    "Lemaire",
    "Moretti",
    "Novak",
    "Okafor",
    "Petrov",
    "Quinn",
    "Rossi",
    "Silva",
    "Tanaka",
    "Vidal",
    "Weber",
    "Yildiz",
    "Zielinski",
]
NATIONALITIES = [
    "England",
    "Spain",
    "Italy",
    "Germany",
    "France",
    "Brazil",
    "Turkey",
    "Portugal",
    "Netherlands",
    "Argentina",
]

LEAGUES = {
    "PL": (
        "Premier League",
        "England",
        2021,
        [
            ("Arsenal FC", "ARS"),
            ("Aston Villa FC", "AVL"),
            ("AFC Bournemouth", "BOU"),
            ("Brentford FC", "BRE"),
            ("Brighton & Hove Albion FC", "BHA"),
            ("Burnley FC", "BUR"),
            ("Chelsea FC", "CHE"),
            ("Crystal Palace FC", "CRY"),
            ("Everton FC", "EVE"),
            ("Fulham FC", "FUL"),
            ("Leeds United FC", "LEE"),
            ("Liverpool FC", "LIV"),
            ("Manchester City FC", "MCI"),
            ("Manchester United FC", "MUN"),
            ("Newcastle United FC", "NEW"),
            ("Nottingham Forest FC", "NFO"),
            ("Sunderland AFC", "SUN"),
            ("Tottenham Hotspur FC", "TOT"),
            ("West Ham United FC", "WHU"),
            ("Wolverhampton Wanderers FC", "WOL"),
        ],
    ),
    "PD": (
        "Primera Division",
        "Spain",
        2014,
        [
            ("Athletic Club", "ATH"),
            ("Club Atlético de Madrid", "ATM"),
            ("CA Osasuna", "OSA"),
            ("RC Celta de Vigo", "CEL"),
            ("Deportivo Alavés", "ALA"),
            ("Elche CF", "ELC"),
            ("FC Barcelona", "FCB"),
            ("Getafe CF", "GET"),
            ("Girona FC", "GIR"),
            ("Levante UD", "LEV"),
            ("RCD Mallorca", "MLL"),
            ("Rayo Vallecano de Madrid", "RAY"),
            ("Real Betis Balompié", "BET"),
            ("Real Madrid CF", "RMA"),
            ("Real Oviedo", "OVI"),
            ("Real Sociedad de Fútbol", "RSO"),
            ("Sevilla FC", "SEV"),
            ("Valencia CF", "VAL"),
            ("Villarreal CF", "VIL"),
            ("RCD Espanyol de Barcelona", "ESP"),
        ],
    ),
    "SA": (
        "Serie A",
        "Italy",
        2019,
        [
            ("Atalanta BC", "ATA"),
            ("Bologna FC 1909", "BOL"),
            ("Cagliari Calcio", "CAG"),
            ("Como 1907", "COM"),
            ("US Cremonese", "CRE"),
            ("ACF Fiorentina", "FIO"),
            ("Genoa CFC", "GEN"),
            ("Hellas Verona FC", "HEL"),
            ("FC Internazionale Milano", "INT"),
            ("Juventus FC", "JUV"),
            ("SS Lazio", "LAZ"),
            ("US Lecce", "LEC"),
            ("AC Milan", "MIL"),
            ("SSC Napoli", "NAP"),
            ("Parma Calcio 1913", "PAR"),
            ("AC Pisa 1909", "PIS"),
            ("AS Roma", "ROM"),
            ("US Sassuolo Calcio", "SAS"),
            ("Torino FC", "TOR"),
            ("Udinese Calcio", "UDI"),
        ],
    ),
    "BL1": (
        "Bundesliga",
        "Germany",
        2002,
        [
            ("FC Bayern München", "BAY"),
            ("Borussia Dortmund", "BVB"),
            ("RB Leipzig", "RBL"),
            ("Bayer 04 Leverkusen", "B04"),
            ("Eintracht Frankfurt", "SGE"),
            ("VfB Stuttgart", "VFB"),
            ("SC Freiburg", "SCF"),
            ("SV Werder Bremen", "SVW"),
            ("VfL Wolfsburg", "WOB"),
            ("Borussia Mönchengladbach", "BMG"),
            ("TSG 1899 Hoffenheim", "TSG"),
            ("FC Augsburg", "FCA"),
            ("1. FC Union Berlin", "FCU"),
            ("1. FSV Mainz 05", "M05"),
            ("FC St. Pauli 1910", "STP"),
            ("1. FC Köln", "KOE"),
            ("Hamburger SV", "HSV"),
            ("1. FC Heidenheim 1846", "HDH"),
        ],
    ),
    "CL": (
        "UEFA Champions League",
        "Europe",
        2001,
        [
            ("Arsenal FC", "ARS"),
            ("Liverpool FC", "LIV"),
            ("Manchester City FC", "MCI"),
            ("Chelsea FC", "CHE"),
            ("Tottenham Hotspur FC", "TOT"),
            ("Newcastle United FC", "NEW"),
            ("Real Madrid CF", "RMA"),
            ("FC Barcelona", "FCB"),
            ("Club Atlético de Madrid", "ATM"),
            ("Athletic Club", "ATH"),
            ("Villarreal CF", "VIL"),
            ("FC Internazionale Milano", "INT"),
            ("SSC Napoli", "NAP"),
            ("Juventus FC", "JUV"),
            ("Atalanta BC", "ATA"),
            ("FC Bayern München", "BAY"),
            ("Borussia Dortmund", "BVB"),
            ("Bayer 04 Leverkusen", "B04"),
            ("Eintracht Frankfurt", "SGE"),
            ("Paris Saint-Germain FC", "PSG"),
            ("Olympique de Marseille", "OM"),
            ("AS Monaco FC", "ASM"),
            ("Sporting Clube de Portugal", "SCP"),
            ("SL Benfica", "SLB"),
            ("PSV", "PSV"),
            ("AFC Ajax", "AJA"),
            ("Club Brugge KV", "CLB"),
            ("Galatasaray SK", "GAL"),
            ("Olympiacos FC", "OLY"),
            ("Celtic FC", "CEL"),
            ("SK Slavia Praha", "SLA"),
            ("FK Bodø/Glimt", "BOD"),
            ("Qarabağ Ağdam FK", "QAR"),
            ("Royale Union Saint-Gilloise", "USG"),
            ("FC København", "FCK"),
            ("Pafos FC", "PAF"),
        ],
    ),
}

NAME_COUNTRY = {
    n: league[1] for code, league in LEAGUES.items() if code != "CL" for n, _ in league[3]
}
NAME_COUNTRY.update(
    {
        "Paris Saint-Germain FC": "France",
        "Olympique de Marseille": "France",
        "AS Monaco FC": "France",
        "Sporting Clube de Portugal": "Portugal",
        "SL Benfica": "Portugal",
        "PSV": "Netherlands",
        "AFC Ajax": "Netherlands",
        "Club Brugge KV": "Belgium",
        "Galatasaray SK": "Turkey",
        "Olympiacos FC": "Greece",
        "Celtic FC": "Scotland",
        "SK Slavia Praha": "Czechia",
        "FK Bodø/Glimt": "Norway",
        "Qarabağ Ağdam FK": "Azerbaijan",
        "Royale Union Saint-Gilloise": "Belgium",
        "FC København": "Denmark",
        "Pafos FC": "Cyprus",
    }
)
TEAM_IDS: dict[str, int] = {}
MATCH_ID_BASE = {code: 400000 + i * 1000 for i, code in enumerate(LEAGUES)}


def team_id(name: str) -> int:
    return TEAM_IDS.setdefault(name, 1000 + len(TEAM_IDS) + 1)


def team_json(name: str, tla: str, country: str) -> dict:
    return {
        "id": team_id(name),
        "name": name,
        "shortName": name.split(" FC")[0],
        "tla": tla,
        "crest": None,
        "area": {"name": country},
    }


def squad(rng: random.Random, tid: int) -> list[dict]:
    players = []
    for i, position in enumerate(SQUAD_POSITIONS):
        players.append(
            {
                "id": tid * 100 + i,
                "name": f"{rng.choice(FIRST)} {rng.choice(LAST)}",
                "position": position,
                "nationality": rng.choice(NATIONALITIES),
                "dateOfBirth": f"{rng.randint(1991, 2006)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
            }
        )
    return players


def round_robin(teams: list[str]) -> list[list[tuple[str, str]]]:
    """Circle method; returns rounds of (home, away)."""
    pool = list(teams)
    if len(pool) % 2:
        pool.append("")
    rounds = []
    for r in range(len(pool) - 1):
        pairs = [(pool[i], pool[-1 - i]) for i in range(len(pool) // 2)]
        pairs = [(a, b) if (r + i) % 2 == 0 else (b, a) for i, (a, b) in enumerate(pairs)]
        rounds.append([p for p in pairs if "" not in p])
        pool = [pool[0], pool[-1], *pool[1:-1]]
    return rounds


def make_matches(code: str, teams: list[tuple[str, str]], rng: random.Random):
    rounds = round_robin([t[0] for t in teams])[:TOTAL_ROUNDS]
    tla = dict(teams)
    matches, results = [], []
    mid = MATCH_ID_BASE[code]
    for index, fixtures in enumerate(rounds, start=1):
        base = REFERENCE_DATE + timedelta(days=7 * (index - PLAYED_ROUNDS))
        for j, (home, away) in enumerate(fixtures):
            kickoff = (base + timedelta(days=(j % 3) - 1)).replace(
                hour=(13, 15, 17, 19, 20)[j % 5], minute=(0, 30)[j % 2]
            )
            played = kickoff < REFERENCE_DATE
            live = False
            if index == PLAYED_ROUNDS and j == 1 and kickoff.date() == REFERENCE_DATE.date():
                live, played = True, False
            hs, as_ = (
                rng.choices([0, 1, 2, 3, 4], [22, 32, 25, 14, 7])[0],
                rng.choices([0, 1, 2, 3], [30, 38, 22, 10])[0],
            )
            status = "FINISHED" if played else ("IN_PLAY" if live else "TIMED")
            full = (
                {"home": hs, "away": as_}
                if played
                else ({"home": 1, "away": 0} if live else {"home": None, "away": None})
            )
            winner = (
                ("HOME_TEAM" if hs > as_ else "AWAY_TEAM" if as_ > hs else "DRAW")
                if played
                else None
            )
            matches.append(
                {
                    "id": mid,
                    "utcDate": kickoff.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "status": status,
                    "matchday": index,
                    "stage": "LEAGUE_STAGE" if code == "CL" else "REGULAR_SEASON",
                    "venue": f"{home} Stadium",
                    "homeTeam": {
                        "id": team_id(home),
                        "name": home,
                        "shortName": home.split(" FC")[0],
                        "tla": tla[home],
                        "crest": None,
                    },
                    "awayTeam": {
                        "id": team_id(away),
                        "name": away,
                        "shortName": away.split(" FC")[0],
                        "tla": tla[away],
                        "crest": None,
                    },
                    "score": {
                        "winner": winner,
                        "duration": "REGULAR",
                        "fullTime": full,
                        "halfTime": {"home": hs // 2, "away": as_ // 2}
                        if played
                        else {"home": None, "away": None},
                    },
                }
            )
            mid += 1
            if played:
                results.append((home, away, hs, as_))
    return matches, results


def make_table(teams: list[tuple[str, str]], results) -> list[dict]:
    rows = {n: {"w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "form": []} for n, _ in teams}
    for home, away, hs, as_ in results:
        for me, _other, gf, ga in ((home, away, hs, as_), (away, home, as_, hs)):
            r = rows[me]
            r["gf"] += gf
            r["ga"] += ga
            key = "w" if gf > ga else "d" if gf == ga else "l"
            r[key] += 1
            r["form"].append(key.upper() if key != "d" else "D")
    ordered = sorted(
        teams,
        key=lambda t: (
            -(rows[t[0]]["w"] * 3 + rows[t[0]]["d"]),
            -(rows[t[0]]["gf"] - rows[t[0]]["ga"]),
            -rows[t[0]]["gf"],
            t[0],
        ),
    )
    table = []
    for pos, (name, tla) in enumerate(ordered, start=1):
        r = rows[name]
        table.append(
            {
                "position": pos,
                "team": {
                    "id": team_id(name),
                    "name": name,
                    "shortName": name.split(" FC")[0],
                    "tla": tla,
                    "crest": None,
                },
                "playedGames": r["w"] + r["d"] + r["l"],
                "form": ",".join(r["form"][-5:]) or None,
                "won": r["w"],
                "draw": r["d"],
                "lost": r["l"],
                "points": r["w"] * 3 + r["d"],
                "goalsFor": r["gf"],
                "goalsAgainst": r["ga"],
                "goalDifference": r["gf"] - r["ga"],
            }
        )
    return table


def write(name: str, payload: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


def main() -> None:
    meta = {
        "reference_date": REFERENCE_DATE.date().isoformat(),
        "note": "Synthetic sample data in football-data.org v4 format.",
    }
    competitions = []
    for code, (name, country, cid, teams) in LEAGUES.items():
        rng = random.Random(code)
        competitions.append(
            {
                "id": cid,
                "name": name,
                "code": code,
                "type": "LEAGUE",
                "emblem": None,
                "area": {"name": country},
                "currentSeason": {"startDate": SEASON_START, "endDate": SEASON_END},
            }
        )
        team_rows = [team_json(n, t, NAME_COUNTRY[n]) for n, t in teams]
        for row in team_rows:
            row["squad"] = squad(random.Random(row["id"]), row["id"])
        write(f"{code}_teams", {"_fixture": meta, "count": len(team_rows), "teams": team_rows})
        matches, results = make_matches(code, teams, rng)
        write(f"{code}_matches", {"_fixture": meta, "matches": matches})
        stage = "LEAGUE_STAGE" if code == "CL" else "REGULAR_SEASON"
        write(
            f"{code}_standings",
            {
                "_fixture": meta,
                "standings": [
                    {
                        "stage": stage,
                        "type": "TOTAL",
                        "group": None,
                        "table": make_table(teams, results),
                    }
                ],
            },
        )
    write(
        "competitions", {"_fixture": meta, "count": len(competitions), "competitions": competitions}
    )


if __name__ == "__main__":
    main()
