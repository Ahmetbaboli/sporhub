/** URL state and pure helpers of the "Bugün" page: date, status filter, featured games. */
import { DEFAULT_TIME_ZONE } from "@/lib/api";
import { dayKey } from "@/lib/format";
import type { SportEvent } from "@/lib/types";

export const STATUS_FILTERS = ["all", "live", "upcoming", "finished"] as const;
export type StatusFilter = (typeof STATUS_FILTERS)[number];

export interface TodayState {
  /** YYYY-MM-DD in the site's default zone; undefined means "today". */
  date?: string;
  status: StatusFilter;
}

const DATE_RE = /^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/;
const MS_PER_DAY = 86_400_000;
const FEATURED_LIMIT = 3;

/**
 * Featured order, stated openly instead of an invented "importance" score: live games first,
 * then these competitions in this order, then kick-off time. Unknown leagues come last.
 */
export const FEATURED_COMPETITIONS = [
  "uefa-champions-league",
  "super-lig",
  "premier-league",
  "primera-division",
  "serie-a",
  "bundesliga",
  "ligue-1",
  "nba",
  "eredivisie",
  "primeira-liga",
  "championship",
  "campeonato-brasileiro-serie-a",
];

type Params = Record<string, string | string[] | undefined>;

function one(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export function todayKey(now: Date = new Date(), timeZone = DEFAULT_TIME_ZONE): string {
  return dayKey(now.toISOString(), timeZone);
}

export function parseTodayState(params: Params, now: Date = new Date()): TodayState {
  const date = one(params.date);
  const status = one(params.status);
  const valid =
    date && DATE_RE.test(date) && !Number.isNaN(Date.parse(`${date}T00:00:00Z`));
  return {
    date: valid && date !== todayKey(now) ? date : undefined,
    status: STATUS_FILTERS.includes(status as StatusFilter)
      ? (status as StatusFilter)
      : "all",
  };
}

/** YYYY-MM-DD shifted by whole days (calendar arithmetic in UTC, so no DST surprises). */
export function shiftDay(day: string, days: number): string {
  return new Date(Date.parse(`${day}T00:00:00Z`) + days * MS_PER_DAY)
    .toISOString()
    .slice(0, 10);
}

export function todayHref(state: TodayState, change: Partial<TodayState> = {}): string {
  const next = { ...state, ...change };
  const params = new URLSearchParams();
  if (next.date && next.date !== todayKey()) params.set("date", next.date);
  if (next.status !== "all") params.set("status", next.status);
  const query = params.toString();
  return query ? `/?${query}` : "/";
}

export function matchesStatus(event: SportEvent, status: StatusFilter): boolean {
  switch (status) {
    case "live":
      return event.status === "live";
    case "upcoming":
      return event.status === "scheduled" || event.status === "postponed";
    case "finished":
      return event.status === "finished" || event.status === "cancelled";
    default:
      return true;
  }
}

export function countByStatus(events: SportEvent[]): Record<StatusFilter, number> {
  return Object.fromEntries(
    STATUS_FILTERS.map((s) => [s, events.filter((e) => matchesStatus(e, s)).length]),
  ) as Record<StatusFilter, number>;
}

function competitionRank(event: SportEvent): number {
  const index = FEATURED_COMPETITIONS.indexOf(event.competition.slug);
  return index === -1 ? FEATURED_COMPETITIONS.length : index;
}

/** Up to three two-sided games worth putting on top (see FEATURED_COMPETITIONS). */
export function pickFeatured(events: SportEvent[], limit = FEATURED_LIMIT): SportEvent[] {
  return events
    .filter((e) => e.kind === "match" && e.status !== "cancelled")
    .filter((e) => competitionRank(e) < FEATURED_COMPETITIONS.length)
    .map((e, index) => ({ e, index }))
    .sort(
      (a, b) =>
        Number(b.e.status === "live") - Number(a.e.status === "live") ||
        competitionRank(a.e) - competitionRank(b.e) ||
        a.e.start_time.localeCompare(b.e.start_time) ||
        a.index - b.index,
    )
    .slice(0, limit)
    .map(({ e }) => e);
}

/** Events touching the visitor's favourites: followed match, team or league. */
export function tribuneEvents(
  events: SportEvent[],
  tribune: { teams: number[]; competitions: number[]; matches: number[] },
): SportEvent[] {
  return events.filter(
    (e) =>
      tribune.matches.includes(e.id) ||
      tribune.competitions.includes(e.competition.id) ||
      e.participants.some((p) => p.team && tribune.teams.includes(p.team.id)),
  );
}
