/**
 * The single typed client for the Just Sport API. Every network call in the web app goes
 * through this module; the frontend never talks to external sports APIs.
 */
import type {
  AdminStatus,
  ApiErrorBody,
  Competition,
  CompetitionDetail,
  CompetitionStats,
  Dashboard,
  EventStatus,
  FavoriteIds,
  FavoriteKind,
  Favorites,
  HeadToHead,
  MatchDetails,
  MatchForecast,
  Meta,
  NewsArchive,
  NewsCategoryFilter,
  NewsItem,
  Page,
  Player,
  SearchResults,
  Sport,
  SportEvent,
  PlayerStatsList,
  Standing,
  StandingEntry,
  SeasonForecast,
  TeamAnalysis,
  TeamDetail,
} from "@/lib/types";

export const DEFAULT_TIME_ZONE = "Europe/Istanbul";
export const REVALIDATE_SECONDS = 60;
const REQUEST_TIMEOUT_MS = 8000;
const DEFAULT_API_URL = "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function apiBaseUrl(): string {
  // The server may reach the API through a private hostname (Docker network).
  const internal =
    typeof window === "undefined" ? process.env.API_INTERNAL_URL : undefined;
  return (internal || process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL).replace(
    /\/$/,
    "",
  );
}

type Query = Record<string, string | number | readonly string[] | undefined>;

export function buildUrl(path: string, query: Query = {}): string {
  const url = new URL(`${apiBaseUrl()}${path}`);
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === "") continue;
    const values = Array.isArray(value) ? value : [value];
    for (const v of values) url.searchParams.append(key, String(v));
  }
  return url.toString();
}

async function parseError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as ApiErrorBody;
    return new ApiError(response.status, body.error.code, body.error.message);
  } catch {
    return new ApiError(
      response.status,
      "http_error",
      response.statusText || "İstek başarısız",
    );
  }
}

async function send(url: string, init: RequestInit): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
  } catch {
    throw new ApiError(503, "unreachable", "API'ye ulaşılamıyor");
  }
  if (!response.ok) throw await parseError(response);
  return response;
}

async function get<T>(path: string, query?: Query): Promise<T> {
  const response = await send(buildUrl(path, query), {
    headers: { Accept: "application/json" },
    next: { revalidate: REVALIDATE_SECONDS },
  });
  return (await response.json()) as T;
}

/** Per-user request: never cached, authorized with a short-lived bearer token. */
async function authed<T>(
  token: string,
  path: string,
  method: "GET" | "PUT" | "DELETE" = "GET",
): Promise<T | undefined> {
  const response = await send(buildUrl(path), {
    method,
    headers: { Accept: "application/json", Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  return response.status === 204 ? undefined : ((await response.json()) as T);
}

/** Admin-only request; the token is a server-side secret and never reaches the browser. */
async function adminGet<T>(path: string, adminToken: string): Promise<T> {
  const response = await send(buildUrl(path), {
    headers: { Accept: "application/json", "X-Admin-Token": adminToken },
    cache: "no-store",
  });
  return (await response.json()) as T;
}

function favoritePath(kind: FavoriteKind, id: number): string {
  return `/api/v1/me/favorites/${kind}/${id}`;
}

export interface EventsQuery {
  status?: EventStatus[];
  from?: string;
  to?: string;
  order?: "asc" | "desc";
  page?: number;
  pageSize?: number;
}

export interface NewsQuery {
  category?: NewsCategoryFilter;
  sport?: string;
  team?: number;
  player?: number;
  competition?: number;
  breaking?: boolean;
  month?: string;
  q?: string;
  maxAgeHours?: number;
  page?: number;
  pageSize?: number;
}

function newsParams(q: NewsQuery): Query {
  return {
    category: q.category,
    sport: q.sport,
    team: q.team,
    player: q.player,
    competition: q.competition,
    breaking: q.breaking === undefined ? undefined : String(q.breaking),
    month: q.month,
    q: q.q,
    max_age_hours: q.maxAgeHours,
    page: q.page,
    page_size: q.pageSize,
  };
}

export const api = {
  meta: () => get<Meta>("/api/v1/meta"),
  sports: () => get<Page<Sport>>("/api/v1/sports"),
  competitions: (sport: string) =>
    get<Page<Competition>>(`/api/v1/sports/${encodeURIComponent(sport)}/competitions`),
  competition: (ref: string) =>
    get<CompetitionDetail>(`/api/v1/competitions/${encodeURIComponent(ref)}`),
  competitionEvents: (ref: string, q: EventsQuery = {}) =>
    get<Page<SportEvent>>(`/api/v1/competitions/${encodeURIComponent(ref)}/events`, {
      status: q.status,
      from: q.from,
      to: q.to,
      order: q.order,
      page: q.page,
      page_size: q.pageSize,
    }),
  competitionForecast: (ref: string) =>
    get<SeasonForecast>(`/api/v1/competitions/${encodeURIComponent(ref)}/forecast`),
  matchForecast: (id: number) => get<MatchForecast>(`/api/v1/events/${id}/forecast`),
  competitionStats: (ref: string) =>
    get<CompetitionStats>(`/api/v1/competitions/${encodeURIComponent(ref)}/stats`),
  standings: (ref: string) =>
    get<Page<Standing>>(`/api/v1/competitions/${encodeURIComponent(ref)}/standings`),
  todayEvents: (opts: { sport?: string; date?: string; tz?: string } = {}) =>
    get<Page<SportEvent>>("/api/v1/events/today", {
      sport: opts.sport,
      date: opts.date,
      tz: opts.tz ?? DEFAULT_TIME_ZONE,
    }),
  event: (id: number) => get<SportEvent>(`/api/v1/events/${id}`),
  matchDetails: (id: number) => get<MatchDetails>(`/api/v1/events/${id}/details`),
  team: (id: number) => get<TeamDetail>(`/api/v1/teams/${id}`),
  teamEvents: (id: number, q: Pick<EventsQuery, "order" | "page" | "pageSize"> = {}) =>
    get<Page<SportEvent>>(`/api/v1/teams/${id}/events`, {
      order: q.order,
      page: q.page,
      page_size: q.pageSize,
    }),
  player: (id: number) => get<Player>(`/api/v1/players/${id}`),
  teamAnalysis: (id: number, last?: number) =>
    get<TeamAnalysis>(`/api/v1/teams/${id}/analysis`, { last }),
  headToHead: (id: number, opponentId: number, limit?: number) =>
    get<HeadToHead>(`/api/v1/teams/${id}/h2h/${opponentId}`, { limit }),
  teamStandings: (id: number) =>
    get<Page<StandingEntry>>(`/api/v1/teams/${id}/standings`),
  playerStandings: (id: number) =>
    get<Page<StandingEntry>>(`/api/v1/players/${id}/standings`),
  playerEvents: (id: number, q: Pick<EventsQuery, "order" | "pageSize"> = {}) =>
    get<Page<SportEvent>>(`/api/v1/players/${id}/events`, {
      order: q.order,
      page_size: q.pageSize,
    }),
  playerStats: (id: number) => get<PlayerStatsList>(`/api/v1/players/${id}/stats`),
  news: (q: NewsQuery = {}) => get<Page<NewsItem>>("/api/v1/news", newsParams(q)),
  newsArchive: (q: Omit<NewsQuery, "month" | "page" | "pageSize"> = {}) =>
    get<NewsArchive>("/api/v1/news/archive", newsParams(q)),
  newsArticle: (id: number) => get<NewsItem>(`/api/v1/news/${id}`),
  search: (q: string) => get<SearchResults>("/api/v1/search", { q }),
  admin: {
    status: (adminToken: string) =>
      adminGet<AdminStatus>("/api/v1/admin/status", adminToken),
  },
  me: {
    favoriteIds: async (token: string) =>
      (await authed<FavoriteIds>(token, "/api/v1/me/favorites/ids"))!,
    favorites: async (token: string) =>
      (await authed<Favorites>(token, "/api/v1/me/favorites"))!,
    dashboard: async (token: string) =>
      (await authed<Dashboard>(token, "/api/v1/me/dashboard"))!,
    addFavorite: (token: string, kind: FavoriteKind, id: number) =>
      authed<void>(token, favoritePath(kind, id), "PUT"),
    removeFavorite: (token: string, kind: FavoriteKind, id: number) =>
      authed<void>(token, favoritePath(kind, id), "DELETE"),
    deleteAccount: (token: string) => authed<void>(token, "/api/v1/me", "DELETE"),
  },
};
