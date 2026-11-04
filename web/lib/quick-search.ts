/** Ctrl+K quick search: result flattening, keyboard shortcut and the fetch to our own route. */
import type { SearchResults } from "@/lib/types";

export const MIN_QUICK_QUERY = 2;
/** Rows per group; the full list is one Enter away on /search. */
export const QUICK_GROUP_LIMIT = 5;
export const QUICK_ROUTE = "/api/quick-search";

export type QuickKind = "competition" | "team" | "player" | "all";

export interface QuickItem {
  key: string;
  kind: QuickKind;
  href: string;
  title: string;
  subtitle: string | null;
  logo_url: string | null;
  short_name?: string | null;
}

export function searchPageHref(q: string): string {
  return `/search?q=${encodeURIComponent(q.trim())}`;
}

/** One keyboard-navigable list: teams (most searched), leagues, players, then "all results". */
export function flattenResults(results: SearchResults, q: string): QuickItem[] {
  const comps = results.competitions.slice(0, QUICK_GROUP_LIMIT).map((c): QuickItem => ({
    key: `c${c.id}`,
    kind: "competition",
    href: `/${c.sport_slug}/${c.slug}`,
    title: c.name,
    subtitle: c.country,
    logo_url: c.logo_url,
  }));
  const teams = results.teams.slice(0, QUICK_GROUP_LIMIT).map((t): QuickItem => ({
    key: `t${t.id}`,
    kind: "team",
    href: `/teams/${t.id}`,
    title: t.name,
    subtitle: t.country,
    logo_url: t.logo_url,
    short_name: t.short_name,
  }));
  const players = results.players.slice(0, QUICK_GROUP_LIMIT).map((p): QuickItem => ({
    key: `p${p.id}`,
    kind: "player",
    href: `/players/${p.id}`,
    title: p.name,
    subtitle: [p.position, p.team?.name].filter(Boolean).join(" · ") || null,
    logo_url: p.team?.logo_url ?? null,
    short_name: p.team?.short_name,
  }));
  const all: QuickItem = {
    key: "all",
    kind: "all",
    href: searchPageHref(q),
    title: q.trim(),
    subtitle: null,
    logo_url: null,
  };
  return [...teams, ...comps, ...players, all];
}

type ShortcutEvent = Pick<KeyboardEvent, "key" | "ctrlKey" | "metaKey" | "altKey"> & {
  target: EventTarget | null;
};

function isTyping(target: EventTarget | null): boolean {
  if (!target || typeof (target as HTMLElement).tagName !== "string") return false;
  const el = target as HTMLElement;
  return (
    el.isContentEditable ||
    ["INPUT", "TEXTAREA", "SELECT"].includes(el.tagName.toUpperCase())
  );
}

/** Ctrl+K / ⌘K anywhere; "/" too, unless the user is typing in a field. */
export function isOpenShortcut(e: ShortcutEvent): boolean {
  if (e.altKey) return false;
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") return true;
  return e.key === "/" && !e.ctrlKey && !e.metaKey && !isTyping(e.target);
}

export const EMPTY_RESULTS: Omit<SearchResults, "query"> = {
  competitions: [],
  teams: [],
  players: [],
};

export async function fetchQuickResults(
  q: string,
  signal: AbortSignal,
): Promise<SearchResults> {
  const response = await fetch(`${QUICK_ROUTE}?q=${encodeURIComponent(q)}`, { signal });
  if (!response.ok) throw new Error(`quick search ${response.status}`);
  return (await response.json()) as SearchResults;
}
