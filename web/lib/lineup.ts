import type { Lineup, LineupPlayer } from "@/lib/types";

const OUTFIELD_PLAYERS = 10;

/**
 * Depth on the pitch from the provider's position code (ESPN: G, CD-L, RB, DM, AM-R, CF…):
 * keeper 0 → forwards 5. The provider's own "formation place" numbers are not ordered by line.
 */
export function roleRank(position: string | null): number {
  const code = (position ?? "").toUpperCase();
  const base = code.split("-")[0];
  if (base === "G" || base === "GK") return 0;
  if (base === "CD" || base === "CB" || base.endsWith("B")) return 1;
  if (base === "DM") return 2;
  if (base === "AM") return 4;
  if (base.includes("M")) return 3;
  return 5;
}

/** Left (0) to right (4) as the team sees the pitch. */
export function lateral(position: string | null): number {
  const code = (position ?? "").toUpperCase();
  const base = code.split("-")[0];
  if (["LB", "LWB", "LM", "LW"].includes(base)) return 0;
  if (["RB", "RWB", "RM", "RW"].includes(base)) return 4;
  if (code.endsWith("-L")) return 1;
  if (code.endsWith("-R")) return 3;
  return 2;
}

/**
 * Starters split into pitch lines, keeper first: "4-2-3-1" → [1, 4, 2, 3, 1] players, each
 * line left to right. Null when the formation and the starters do not add up (show a list).
 */
export function formationLines(lineup: Lineup): LineupPlayer[][] | null {
  const sizes = (lineup.formation ?? "").split("-").map(Number);
  if (!sizes.length || sizes.some((n) => !Number.isInteger(n) || n <= 0)) return null;
  if (sizes.reduce((a, b) => a + b, 0) !== OUTFIELD_PLAYERS) return null;
  if (lineup.starters.length !== OUTFIELD_PLAYERS + 1) return null;
  const ordered = [...lineup.starters].sort(
    (a, b) =>
      roleRank(a.position) - roleRank(b.position) ||
      lateral(a.position) - lateral(b.position),
  );
  const lines: LineupPlayer[][] = [ordered.slice(0, 1)];
  let next = 1;
  for (const size of sizes) {
    const line = ordered.slice(next, next + size);
    lines.push(line.sort((a, b) => lateral(a.position) - lateral(b.position)));
    next += size;
  }
  return lines;
}

/** "Matteo Guendouzi" → "Guendouzi" for the pitch, where space is tight. */
export function pitchName(name: string): string {
  const parts = name.trim().split(/\s+/);
  return parts.length > 1 ? parts[parts.length - 1] : name;
}
