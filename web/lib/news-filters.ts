/** URL state of the /news page (pure: parsed from and written back to search params). */
import type { NewsCategoryFilter } from "@/lib/types";

export const NEWS_TABS = [
  "all",
  "transfer",
  "transfer_official",
  "transfer_rumour",
  "interview",
  "tournament",
  "general",
] as const;
export type NewsTab = (typeof NEWS_TABS)[number];
export const BREAKING_TAB = "breaking";

export interface NewsState {
  tab: NewsTab | typeof BREAKING_TAB;
  sport?: string;
  month?: string;
  q?: string;
  team?: number;
  player?: number;
  competition?: number;
  page: number;
}

type Params = Record<string, string | string[] | undefined>;

const MONTH_RE = /^\d{4}-(0[1-9]|1[0-2])$/;
const SLUG_RE = /^[a-z0-9-]{1,64}$/;
const MIN_QUERY = 2;

function one(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

function positiveInt(value: string | undefined): number | undefined {
  return value && /^\d+$/.test(value) && Number(value) > 0 ? Number(value) : undefined;
}

export function parseNewsState(params: Params): NewsState {
  const tab = one(params.category);
  const sport = one(params.sport);
  const month = one(params.month);
  const q = one(params.q)?.trim();
  return {
    tab:
      tab === BREAKING_TAB
        ? BREAKING_TAB
        : NEWS_TABS.includes(tab as NewsTab)
          ? (tab as NewsTab)
          : "all",
    sport: sport && SLUG_RE.test(sport) ? sport : undefined,
    month: month && MONTH_RE.test(month) ? month : undefined,
    q: q && q.length >= MIN_QUERY ? q.slice(0, 100) : undefined,
    team: positiveInt(one(params.team)),
    player: positiveInt(one(params.player)),
    competition: positiveInt(one(params.competition)),
    page: positiveInt(one(params.page)) ?? 1,
  };
}

/** Link to the page with some filters changed; any change resets to page 1. */
export function newsHref(state: NewsState, change: Partial<NewsState> = {}): string {
  const next = { ...state, page: 1, ...change };
  const params = new URLSearchParams();
  if (next.tab !== "all") params.set("category", next.tab);
  for (const key of ["sport", "month", "q", "team", "player", "competition"] as const) {
    const value = next[key];
    if (value !== undefined && value !== "") params.set(key, String(value));
  }
  if (next.page > 1) params.set("page", String(next.page));
  const query = params.toString();
  return query ? `/news?${query}` : "/news";
}

export function apiCategory(tab: NewsState["tab"]): NewsCategoryFilter | undefined {
  return tab === "all" || tab === BREAKING_TAB ? undefined : tab;
}
