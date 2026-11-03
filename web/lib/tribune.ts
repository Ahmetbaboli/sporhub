/**
 * "Benim Tribünüm": favourite teams, leagues, drivers and followed matches without an account.
 * Only numeric ids live on the device, in one cookie, so server components can put the
 * matching content first. Pure helpers here; the cookie is read in lib/tribune-server.ts and
 * written by the client provider (components/tribune/tribune-provider.tsx).
 */
export const TRIBUNE_COOKIE = "js-tribun";
export const TRIBUNE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365;
const MAX_PER_KIND = 50;

export const TRIBUNE_KINDS = ["teams", "competitions", "players", "matches"] as const;
export type TribuneKind = (typeof TRIBUNE_KINDS)[number];
export type Tribune = Record<TribuneKind, number[]>;

const PREFIX: Record<TribuneKind, string> = {
  teams: "t",
  competitions: "c",
  players: "p",
  matches: "m",
};

export function emptyTribune(): Tribune {
  return { teams: [], competitions: [], players: [], matches: [] };
}

/** "t:1.2|c:4|m:9" -> ids per kind; anything malformed is dropped, never thrown. */
export function parseTribune(raw: string | undefined | null): Tribune {
  const tribune = emptyTribune();
  if (!raw) return tribune;
  for (const part of decodeURIComponent(raw).split("|")) {
    const [prefix, ids = ""] = part.split(":");
    const kind = TRIBUNE_KINDS.find((k) => PREFIX[k] === prefix);
    if (!kind) continue;
    const unique = new Set(
      ids
        .split(".")
        .filter((id) => /^\d{1,10}$/.test(id))
        .map(Number)
        .filter((id) => id > 0),
    );
    tribune[kind] = [...unique].slice(0, MAX_PER_KIND);
  }
  return tribune;
}

export function serializeTribune(tribune: Tribune): string {
  return TRIBUNE_KINDS.filter((k) => tribune[k].length > 0)
    .map((k) => `${PREFIX[k]}:${tribune[k].slice(0, MAX_PER_KIND).join(".")}`)
    .join("|");
}

/** Adds or removes one id; newest first so recent picks show first. */
export function toggleInTribune(
  tribune: Tribune,
  kind: TribuneKind,
  id: number,
): Tribune {
  const list = tribune[kind];
  const next = list.includes(id) ? list.filter((x) => x !== id) : [id, ...list];
  return { ...tribune, [kind]: next.slice(0, MAX_PER_KIND) };
}

export function isTribuneEmpty(tribune: Tribune): boolean {
  return TRIBUNE_KINDS.every((k) => tribune[k].length === 0);
}

/** Stable sort: items whose key is in `ids` first (in `ids` order), the rest as they came. */
export function prioritize<T>(
  items: T[],
  ids: number[],
  keyOf: (item: T) => number[],
): T[] {
  const rank = (item: T) => {
    const hits = keyOf(item)
      .map((k) => ids.indexOf(k))
      .filter((i) => i >= 0);
    return hits.length ? Math.min(...hits) : Number.POSITIVE_INFINITY;
  };
  return items
    .map((item, index) => ({ item, index, rank: rank(item) }))
    .sort((a, b) => a.rank - b.rank || a.index - b.index)
    .map(({ item }) => item);
}
