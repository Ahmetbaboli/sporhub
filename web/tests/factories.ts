import type { Competition, Participant, SportEvent, Standing, Team } from "@/lib/types";

export const team = (id: number, name: string, extra: Partial<Team> = {}): Team => ({
  id,
  name,
  short_name: name.slice(0, 3).toUpperCase(),
  logo_url: null,
  country: "England",
  sport_slug: "football",
  ...extra,
});

export const competition = (extra: Partial<Competition> = {}): Competition => ({
  id: 1,
  slug: "premier-league",
  name: "Premier League",
  sport_slug: "football",
  country: "England",
  logo_url: null,
  ...extra,
});

const participant = (
  t: Team,
  side: "home" | "away",
  score: number | null,
): Participant => ({
  team: t,
  player: null,
  side,
  score,
  position: null,
  points: null,
  extra: {},
});

export const event = (extra: Partial<SportEvent> = {}): SportEvent => ({
  id: 1,
  kind: "match",
  name: null,
  start_time: "2026-10-26T17:30:00Z",
  status: "finished",
  venue: null,
  round: "9",
  competition: competition(),
  season: "2026/27",
  participants: [
    participant(team(1, "Arsenal FC"), "home", 2),
    participant(team(2, "Chelsea FC"), "away", 1),
  ],
  extra: {},
  ...extra,
});

export const standing = (position: number, t: Team, points: number): Standing => ({
  position,
  team: t,
  player: null,
  played: 9,
  won: 6,
  drawn: 1,
  lost: 2,
  points,
  extra: { goals_for: 18, goals_against: 9, goal_difference: 9, form: "W,W,D,L,W" },
});
