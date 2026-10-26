/**
 * The single typed client for the Just Sport API. Every network call in the web app goes
 * through this module; the frontend never talks to external sports APIs.
 */
import type {
  ApiErrorBody,
  Competition,
  CompetitionDetail,
  EventStatus,
  Page,
  Player,
  SearchResults,
  Sport,
  SportEvent,
  Standing,
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

async function get<T>(path: string, query?: Query): Promise<T> {
  let response: Response;
  try {
    response = await fetch(buildUrl(path, query), {
      headers: { Accept: "application/json" },
      next: { revalidate: REVALIDATE_SECONDS },
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
  } catch {
    throw new ApiError(503, "unreachable", "API'ye ulaşılamıyor");
  }
  if (!response.ok) throw await parseError(response);
  return (await response.json()) as T;
}

export interface EventsQuery {
  status?: EventStatus[];
  from?: string;
  to?: string;
  order?: "asc" | "desc";
  page?: number;
  pageSize?: number;
}

export const api = {
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
  standings: (ref: string) =>
    get<Page<Standing>>(`/api/v1/competitions/${encodeURIComponent(ref)}/standings`),
  todayEvents: (opts: { sport?: string; date?: string; tz?: string } = {}) =>
    get<Page<SportEvent>>("/api/v1/events/today", {
      sport: opts.sport,
      date: opts.date,
      tz: opts.tz ?? DEFAULT_TIME_ZONE,
    }),
  event: (id: number) => get<SportEvent>(`/api/v1/events/${id}`),
  team: (id: number) => get<TeamDetail>(`/api/v1/teams/${id}`),
  teamEvents: (id: number, q: Pick<EventsQuery, "order" | "page" | "pageSize"> = {}) =>
    get<Page<SportEvent>>(`/api/v1/teams/${id}/events`, {
      order: q.order,
      page: q.page,
      page_size: q.pageSize,
    }),
  player: (id: number) => get<Player>(`/api/v1/players/${id}`),
  search: (q: string) => get<SearchResults>("/api/v1/search", { q }),
};
