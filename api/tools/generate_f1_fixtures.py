"""Generates deterministic sample fixtures in the raw Jolpica-F1 (Ergast) JSON format.

Constructors, drivers and the calendar are real-world names; results are synthetic.
Run:  uv run python tools/generate_f1_fixtures.py
"""

import json
import random
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "fixtures" / "jolpica"
SEASON = "2026"
# The sample "today" is the Mexican GP race day; rounds before it are completed.
REFERENCE_DATE = "2026-11-01"
COMPLETED_ROUNDS = 19
POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]

CONSTRUCTORS = {
    "mercedes": ("Mercedes", "German"),
    "ferrari": ("Ferrari", "Italian"),
    "mclaren": ("McLaren", "British"),
    "red_bull": ("Red Bull", "Austrian"),
    "williams": ("Williams", "British"),
    "rb": ("RB F1 Team", "Italian"),
    "aston_martin": ("Aston Martin", "British"),
    "haas": ("Haas F1 Team", "American"),
    "audi": ("Audi", "German"),
    "alpine": ("Alpine F1 Team", "French"),
    "cadillac": ("Cadillac F1 Team", "American"),
}
# (driverId, given, family, code, number, dob, nationality, constructor, strength)
DRIVERS = [
    ("russell", "George", "Russell", "RUS", "63", "1998-02-15", "British", "mercedes", 9.2),
    ("antonelli", "Kimi", "Antonelli", "ANT", "12", "2006-08-25", "Italian", "mercedes", 8.8),
    ("leclerc", "Charles", "Leclerc", "LEC", "16", "1997-10-16", "Monegasque", "ferrari", 9.0),
    ("hamilton", "Lewis", "Hamilton", "HAM", "44", "1985-01-07", "British", "ferrari", 8.7),
    ("norris", "Lando", "Norris", "NOR", "1", "1999-11-13", "British", "mclaren", 9.1),
    ("piastri", "Oscar", "Piastri", "PIA", "81", "2001-04-06", "Australian", "mclaren", 8.9),
    ("max_verstappen", "Max", "Verstappen", "VER", "3", "1997-09-30", "Dutch", "red_bull", 9.3),
    ("hadjar", "Isack", "Hadjar", "HAD", "6", "2004-09-28", "French", "red_bull", 7.6),
    ("albon", "Alexander", "Albon", "ALB", "23", "1996-03-23", "Thai", "williams", 7.7),
    ("sainz", "Carlos", "Sainz", "SAI", "55", "1994-09-01", "Spanish", "williams", 8.0),
    ("lawson", "Liam", "Lawson", "LAW", "30", "2002-02-11", "New Zealander", "rb", 7.4),
    ("lindblad", "Arvid", "Lindblad", "LIN", "41", "2007-08-08", "British", "rb", 7.0),
    ("alonso", "Fernando", "Alonso", "ALO", "14", "1981-07-29", "Spanish", "aston_martin", 7.9),
    ("stroll", "Lance", "Stroll", "STR", "18", "1998-10-29", "Canadian", "aston_martin", 6.9),
    ("ocon", "Esteban", "Ocon", "OCO", "31", "1996-09-17", "French", "haas", 7.3),
    ("bearman", "Oliver", "Bearman", "BEA", "87", "2005-05-08", "British", "haas", 7.5),
    ("hulkenberg", "Nico", "Hülkenberg", "HUL", "27", "1987-08-19", "German", "audi", 7.4),
    ("bortoleto", "Gabriel", "Bortoleto", "BOR", "5", "2004-10-14", "Brazilian", "audi", 7.1),
    ("gasly", "Pierre", "Gasly", "GAS", "10", "1996-02-07", "French", "alpine", 7.5),
    ("colapinto", "Franco", "Colapinto", "COL", "43", "2003-05-27", "Argentine", "alpine", 7.0),
    ("perez", "Sergio", "Pérez", "PER", "11", "1990-01-26", "Mexican", "cadillac", 7.2),
    ("bottas", "Valtteri", "Bottas", "BOT", "77", "1989-08-28", "Finnish", "cadillac", 7.0),
]
# (raceName, circuitId, circuitName, locality, country, lat, long, date, time)
CALENDAR = [
    (
        "Australian Grand Prix",
        "albert_park",
        "Albert Park Grand Prix Circuit",
        "Melbourne",
        "Australia",
        "-37.8497",
        "144.968",
        "2026-03-08",
        "04:00:00Z",
    ),
    (
        "Chinese Grand Prix",
        "shanghai",
        "Shanghai International Circuit",
        "Shanghai",
        "China",
        "31.3389",
        "121.22",
        "2026-03-15",
        "07:00:00Z",
    ),
    (
        "Japanese Grand Prix",
        "suzuka",
        "Suzuka Circuit",
        "Suzuka",
        "Japan",
        "34.8431",
        "136.541",
        "2026-03-29",
        "05:00:00Z",
    ),
    (
        "Bahrain Grand Prix",
        "bahrain",
        "Bahrain International Circuit",
        "Sakhir",
        "Bahrain",
        "26.0325",
        "50.5106",
        "2026-04-12",
        "15:00:00Z",
    ),
    (
        "Saudi Arabian Grand Prix",
        "jeddah",
        "Jeddah Corniche Circuit",
        "Jeddah",
        "Saudi Arabia",
        "21.6319",
        "39.1044",
        "2026-04-19",
        "17:00:00Z",
    ),
    (
        "Miami Grand Prix",
        "miami",
        "Miami International Autodrome",
        "Miami",
        "USA",
        "25.9581",
        "-80.2389",
        "2026-05-03",
        "20:00:00Z",
    ),
    (
        "Canadian Grand Prix",
        "villeneuve",
        "Circuit Gilles Villeneuve",
        "Montreal",
        "Canada",
        "45.5",
        "-73.5228",
        "2026-05-24",
        "18:00:00Z",
    ),
    (
        "Monaco Grand Prix",
        "monaco",
        "Circuit de Monaco",
        "Monte-Carlo",
        "Monaco",
        "43.7347",
        "7.42056",
        "2026-06-07",
        "13:00:00Z",
    ),
    (
        "Barcelona Grand Prix",
        "catalunya",
        "Circuit de Barcelona-Catalunya",
        "Montmeló",
        "Spain",
        "41.57",
        "2.26111",
        "2026-06-14",
        "13:00:00Z",
    ),
    (
        "Austrian Grand Prix",
        "red_bull_ring",
        "Red Bull Ring",
        "Spielberg",
        "Austria",
        "47.2197",
        "14.7647",
        "2026-06-28",
        "13:00:00Z",
    ),
    (
        "British Grand Prix",
        "silverstone",
        "Silverstone Circuit",
        "Silverstone",
        "UK",
        "52.0786",
        "-1.01694",
        "2026-07-05",
        "14:00:00Z",
    ),
    (
        "Belgian Grand Prix",
        "spa",
        "Circuit de Spa-Francorchamps",
        "Spa",
        "Belgium",
        "50.4372",
        "5.97139",
        "2026-07-19",
        "13:00:00Z",
    ),
    (
        "Hungarian Grand Prix",
        "hungaroring",
        "Hungaroring",
        "Budapest",
        "Hungary",
        "47.5789",
        "19.2486",
        "2026-07-26",
        "13:00:00Z",
    ),
    (
        "Dutch Grand Prix",
        "zandvoort",
        "Circuit Park Zandvoort",
        "Zandvoort",
        "Netherlands",
        "52.3888",
        "4.54092",
        "2026-08-23",
        "13:00:00Z",
    ),
    (
        "Italian Grand Prix",
        "monza",
        "Autodromo Nazionale di Monza",
        "Monza",
        "Italy",
        "45.6156",
        "9.28111",
        "2026-09-06",
        "13:00:00Z",
    ),
    (
        "Madrid Grand Prix",
        "madring",
        "Madring",
        "Madrid",
        "Spain",
        "40.4639",
        "-3.6155",
        "2026-09-13",
        "13:00:00Z",
    ),
    (
        "Azerbaijan Grand Prix",
        "baku",
        "Baku City Circuit",
        "Baku",
        "Azerbaijan",
        "40.3725",
        "49.8533",
        "2026-09-26",
        "11:00:00Z",
    ),
    (
        "Singapore Grand Prix",
        "marina_bay",
        "Marina Bay Street Circuit",
        "Marina Bay",
        "Singapore",
        "1.2914",
        "103.864",
        "2026-10-11",
        "12:00:00Z",
    ),
    (
        "United States Grand Prix",
        "americas",
        "Circuit of the Americas",
        "Austin",
        "USA",
        "30.1328",
        "-97.6411",
        "2026-10-25",
        "19:00:00Z",
    ),
    (
        "Mexico City Grand Prix",
        "rodriguez",
        "Autódromo Hermanos Rodríguez",
        "Mexico City",
        "Mexico",
        "19.4042",
        "-99.0907",
        "2026-11-01",
        "20:00:00Z",
    ),
    (
        "São Paulo Grand Prix",
        "interlagos",
        "Autódromo José Carlos Pace",
        "São Paulo",
        "Brazil",
        "-23.7036",
        "-46.6997",
        "2026-11-08",
        "17:00:00Z",
    ),
    (
        "Las Vegas Grand Prix",
        "vegas",
        "Las Vegas Strip Street Circuit",
        "Las Vegas",
        "USA",
        "36.1147",
        "-115.173",
        "2026-11-21",
        "06:00:00Z",
    ),
    (
        "Qatar Grand Prix",
        "losail",
        "Losail International Circuit",
        "Al Daayen",
        "Qatar",
        "25.49",
        "51.4542",
        "2026-11-29",
        "16:00:00Z",
    ),
    (
        "Abu Dhabi Grand Prix",
        "yas_marina",
        "Yas Marina Circuit",
        "Abu Dhabi",
        "UAE",
        "24.4672",
        "54.6031",
        "2026-12-06",
        "13:00:00Z",
    ),
]
BASE_URL = "https://api.jolpi.ca/ergast/f1"


def mr(table_key: str, table: dict, total: int, **extra: object) -> dict:
    return {
        "_fixture": {
            "reference_date": REFERENCE_DATE,
            "note": "Synthetic sample data in Jolpica-F1 (Ergast) format.",
        },
        "MRData": {
            "xmlns": "",
            "series": "f1",
            "url": f"{BASE_URL}/",
            "limit": str(total),
            "offset": "0",
            "total": str(total),
            table_key: table,
            **extra,
        },
    }


def driver_json(d: tuple) -> dict:
    return {
        "driverId": d[0],
        "permanentNumber": d[4],
        "code": d[3],
        "url": f"https://en.wikipedia.org/wiki/{d[1]}_{d[2]}".replace(" ", "_"),
        "givenName": d[1],
        "familyName": d[2],
        "dateOfBirth": d[5],
        "nationality": d[6],
    }


def constructor_json(cid: str) -> dict:
    name, nationality = CONSTRUCTORS[cid]
    return {
        "constructorId": cid,
        "url": f"https://en.wikipedia.org/wiki/{name.replace(' ', '_')}",
        "name": name,
        "nationality": nationality,
    }


def race_json(index: int, with_sessions: bool) -> dict:
    name, circuit_id, circuit, locality, country, lat, lng, day, time = CALENDAR[index]
    race_date = date.fromisoformat(day)
    race = {
        "season": SEASON,
        "round": str(index + 1),
        "url": f"https://en.wikipedia.org/wiki/{SEASON}_{name.replace(' ', '_')}",
        "raceName": name,
        "Circuit": {
            "circuitId": circuit_id,
            "url": f"https://en.wikipedia.org/wiki/{circuit.replace(' ', '_')}",
            "circuitName": circuit,
            "Location": {"lat": lat, "long": lng, "locality": locality, "country": country},
        },
        "date": day,
        "time": time,
    }
    if with_sessions:
        race["FirstPractice"] = {
            "date": (race_date - timedelta(days=2)).isoformat(),
            "time": "11:30:00Z",
        }
        race["Qualifying"] = {
            "date": (race_date - timedelta(days=1)).isoformat(),
            "time": "15:00:00Z",
        }
    return race


def simulate_race(rng: random.Random) -> list[dict]:
    """Finishing order by strength + noise; a few retirements at the back."""
    scored = sorted(DRIVERS, key=lambda d: -(d[8] + rng.gauss(0, 1.6)))
    grid_order = sorted(DRIVERS, key=lambda d: -(d[8] + rng.gauss(0, 1.2)))
    grid = {d[0]: i + 1 for i, d in enumerate(grid_order)}
    retired = set(rng.sample([d[0] for d in scored[8:]], k=rng.choice([0, 1, 2])))
    classified = [d for d in scored if d[0] not in retired] + [d for d in scored if d[0] in retired]
    rows = []
    for pos, d in enumerate(classified, start=1):
        out = d[0] in retired
        row = {
            "number": d[4],
            "position": str(pos),
            "positionText": "R" if out else str(pos),
            "points": str(POINTS[pos - 1] if pos <= len(POINTS) and not out else 0),
            "Driver": driver_json(d),
            "Constructor": constructor_json(d[7]),
            "grid": str(grid[d[0]]),
            "laps": str(rng.randint(8, 40) if out else 57),
            "status": "Retired" if out else ("Finished" if pos <= 14 else "+1 Lap"),
        }
        if not out and pos <= 14:
            millis = 5_400_000 + rng.randint(0, 600_000) + (pos - 1) * rng.randint(2000, 9000)
            row["Time"] = {
                "millis": str(millis),
                "time": (
                    "1:30:00.000" if pos == 1 else f"+{(pos - 1) * rng.uniform(2.0, 9.0):.3f}s"
                ),
            }
        if not out and pos in (rng.randint(1, 8),):
            row["FastestLap"] = {
                "rank": "1",
                "lap": str(rng.randint(40, 56)),
                "Time": {"time": "1:21.456"},
            }
        rows.append(row)
    return rows


def write(name: str, payload: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )


def main() -> None:
    rng = random.Random(2026)
    races = [race_json(i, with_sessions=i >= COMPLETED_ROUNDS - 2) for i in range(len(CALENDAR))]
    write(f"{SEASON}_races", mr("RaceTable", {"season": SEASON, "Races": races}, len(races)))

    driver_points = {d[0]: [0.0, 0] for d in DRIVERS}
    team_points = {c: [0.0, 0] for c in CONSTRUCTORS}
    results_races = []
    for i in range(COMPLETED_ROUNDS):
        rows = simulate_race(rng)
        for row in rows:
            did = row["Driver"]["driverId"]
            cid = row["Constructor"]["constructorId"]
            pts = float(row["points"])
            driver_points[did][0] += pts
            team_points[cid][0] += pts
            if row["position"] == "1":
                driver_points[did][1] += 1
                team_points[cid][1] += 1
        results_races.append(
            {**race_json(i, with_sessions=i >= COMPLETED_ROUNDS - 2), "Results": rows}
        )
    total_rows = sum(len(r["Results"]) for r in results_races)
    write(
        f"{SEASON}_results", mr("RaceTable", {"season": SEASON, "Races": results_races}, total_rows)
    )

    constructors = [constructor_json(c) for c in CONSTRUCTORS]
    write(
        f"{SEASON}_constructors",
        mr("ConstructorTable", {"season": SEASON, "Constructors": constructors}, len(constructors)),
    )

    by_id = {d[0]: d for d in DRIVERS}
    ranked = sorted(driver_points, key=lambda k: (-driver_points[k][0], -driver_points[k][1], k))
    driver_rows = [
        {
            "position": str(p),
            "positionText": str(p),
            "points": f"{driver_points[k][0]:g}",
            "wins": str(driver_points[k][1]),
            "Driver": driver_json(by_id[k]),
            "Constructors": [constructor_json(by_id[k][7])],
        }
        for p, k in enumerate(ranked, start=1)
    ]
    write(
        f"{SEASON}_driverstandings",
        mr(
            "StandingsTable",
            {
                "season": SEASON,
                "round": str(COMPLETED_ROUNDS),
                "StandingsLists": [
                    {
                        "season": SEASON,
                        "round": str(COMPLETED_ROUNDS),
                        "DriverStandings": driver_rows,
                    }
                ],
            },
            len(driver_rows),
        ),
    )

    ranked_c = sorted(team_points, key=lambda k: (-team_points[k][0], -team_points[k][1], k))
    team_rows = [
        {
            "position": str(p),
            "positionText": str(p),
            "points": f"{team_points[k][0]:g}",
            "wins": str(team_points[k][1]),
            "Constructor": constructor_json(k),
        }
        for p, k in enumerate(ranked_c, start=1)
    ]
    write(
        f"{SEASON}_constructorstandings",
        mr(
            "StandingsTable",
            {
                "season": SEASON,
                "round": str(COMPLETED_ROUNDS),
                "StandingsLists": [
                    {
                        "season": SEASON,
                        "round": str(COMPLETED_ROUNDS),
                        "ConstructorStandings": team_rows,
                    }
                ],
            },
            len(team_rows),
        ),
    )


if __name__ == "__main__":
    main()
