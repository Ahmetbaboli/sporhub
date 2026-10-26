/** Response shapes of the Just Sport API (api/app/schemas/api.py). */

export type EventStatus = "scheduled" | "live" | "finished" | "postponed" | "cancelled";
export type EventKind = "match" | "race" | "session";

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface Sport {
  id: number;
  slug: string;
  name: string;
}

export interface Competition {
  id: number;
  slug: string;
  name: string;
  sport_slug: string;
  country: string | null;
  logo_url: string | null;
}

export interface Season {
  id: number;
  year_label: string;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
}

export interface CompetitionDetail extends Competition {
  current_season: Season | null;
}

export interface Team {
  id: number;
  name: string;
  short_name: string | null;
  logo_url: string | null;
  country: string | null;
  sport_slug: string | null;
}

export interface Player {
  id: number;
  name: string;
  position: string | null;
  nationality: string | null;
  team: Team | null;
  extra: Record<string, unknown>;
}

export interface Participant {
  team: Team | null;
  player: Player | null;
  side: "home" | "away" | null;
  score: number | null;
  position: number | null;
  points: number | null;
  extra: Record<string, unknown>;
}

export interface SportEvent {
  id: number;
  kind: EventKind;
  name: string | null;
  start_time: string;
  status: EventStatus;
  venue: string | null;
  round: string | null;
  competition: Competition;
  season: string;
  participants: Participant[];
  extra: Record<string, unknown>;
}

export interface Standing {
  position: number;
  team: Team | null;
  player: Player | null;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  points: number;
  extra: Record<string, unknown>;
}

export interface TeamDetail extends Team {
  squad: Player[];
}

export interface SearchResults {
  query: string;
  competitions: Competition[];
  teams: Team[];
  players: Player[];
}

export interface ApiErrorBody {
  error: { code: string; message: string };
}
