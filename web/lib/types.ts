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
  source?: string | null;
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

/** Signed-in user shapes (api/app/schemas/me.py). */
export type FavoriteKind = "teams" | "players" | "competitions";

export type FavoriteIds = Record<FavoriteKind, number[]>;

export interface Favorites {
  teams: Team[];
  players: Player[];
  competitions: Competition[];
}

export interface TeamActivity {
  team: Team;
  recent: SportEvent[];
  upcoming: SportEvent[];
}

export interface CompetitionPlace {
  competition: Competition;
  season: Season | null;
  table: Standing[];
  mine: Standing[];
}

export interface Dashboard {
  teams: TeamActivity[];
  competitions: CompetitionPlace[];
}

/** Team analysis (api/app/schemas/analysis.py). */
export type MatchResult = "W" | "D" | "L";

export interface SplitStats {
  played: number;
  won: number;
  drawn: number;
  lost: number;
  scored: number;
  conceded: number;
  win_pct: number;
  avg_scored: number;
  avg_conceded: number;
  clean_sheets: number;
}

export interface FormEntry {
  event_id: number;
  start_time: string;
  competition: string;
  side: "home" | "away";
  opponent: Team;
  scored: number;
  conceded: number;
  result: MatchResult;
}

export interface TeamAnalysis {
  team: Team;
  season: string | null;
  form: FormEntry[];
  form_stats: SplitStats;
  streak: string | null;
  overall: SplitStats;
  home: SplitStats;
  away: SplitStats;
  biggest_win: FormEntry | null;
  biggest_loss: FormEntry | null;
}

export interface HeadToHead {
  team: Team;
  opponent: Team;
  summary: SplitStats;
  matches: SportEvent[];
}

/** Competition statistics (api/app/schemas/stats.py). */
export interface LeaderRow {
  rank: number;
  player: Player | null;
  team: Team | null;
  value: number;
  played: number | null;
}

export interface LeaderCategory {
  key: string;
  subject: "player" | "team";
  rows: LeaderRow[];
}

export interface MatchSummary {
  played: number;
  total_scored: number;
  avg_per_match: number;
  home_win_pct: number;
  draw_pct: number;
  away_win_pct: number;
  biggest_win: SportEvent | null;
  highest_scoring: SportEvent | null;
}

export interface RaceSummary {
  completed: number;
  scheduled: number;
  distinct_winners: number;
  pole_to_win: number;
}

export interface SeasonHistoryRow {
  season: Season;
  leader: Standing | null;
}

export interface CompetitionStats {
  season: Season | null;
  matches: MatchSummary | null;
  races: RaceSummary | null;
  leaders: LeaderCategory[];
  history: SeasonHistoryRow[];
}

export interface StandingEntry {
  competition: Competition;
  season: string;
  standing: Standing;
}

export interface PlayerSeasonStats {
  competition: Competition;
  season: string;
  team: Team | null;
  stats: Record<string, number>;
}

export interface PlayerStatsList {
  player: Player;
  items: PlayerSeasonStats[];
}

/** News (api/app/schemas/news.py). */
export type NewsCategory =
  "general" | "transfer_official" | "transfer_rumour" | "interview" | "tournament";
export type NewsCategoryFilter = NewsCategory | "transfer";

export interface NewsTag {
  kind: "team" | "player" | "competition";
  id: number;
  name: string;
  sport_slug: string | null;
  slug: string | null;
}

export interface NewsItem {
  id: number;
  title: string;
  summary: string;
  url: string;
  image_url: string | null;
  author: string | null;
  source: string;
  published_at: string;
  category: NewsCategory;
  is_breaking: boolean;
  language: string;
  sport_slug: string | null;
  tags: NewsTag[];
}

export interface NewsArchive {
  months: { month: string; count: number }[];
}

/** Data mode and source freshness (api/app/schemas/meta.py). */
export interface SourceMeta {
  name: string;
  sport: string | null;
  configured: boolean;
  last_success_at: string | null;
  last_attempt_at: string | null;
  last_status: string | null;
  stale: boolean;
  scores_delayed: boolean;
}

export interface SportMeta {
  slug: string;
  name: string;
  configured: boolean;
  sources: string[];
}

export interface Meta {
  data_mode: "live" | "demo";
  sports: SportMeta[];
  sources: SourceMeta[];
}

export interface BudgetWindow {
  limit: number;
  used: number;
  remaining: number;
}

export interface SourceStatusDetail extends SourceMeta {
  runs_24h: number;
  failures_24h: number;
  error_rate_24h: number;
  last_error: string | null;
  budget: Record<string, BudgetWindow>;
}

export interface AdminStatus {
  data_mode: "live" | "demo";
  scheduler_enabled: boolean;
  sources: SourceStatusDetail[];
}
