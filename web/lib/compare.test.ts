import { describe, expect, it } from "vitest";
import {
  type CompareMetric,
  formatMetric,
  pairSheets,
  parseCompareType,
  playerMetrics,
  sharedEntry,
  winner,
} from "@/lib/compare";
import type { PlayerSeasonStats, StandingEntry } from "@/lib/types";

const metric = (over: Partial<CompareMetric>): CompareMetric => ({
  key: "goals",
  label: "Gol",
  a: 1,
  b: 2,
  better: "higher",
  format: "int",
  ...over,
});

const comp = (id: number) => ({
  id,
  slug: `c${id}`,
  name: `Lig ${id}`,
  sport_slug: "football",
  country: null,
  logo_url: null,
});

const entry = (competitionId: number, position: number): StandingEntry => ({
  competition: comp(competitionId),
  season: "2026/27",
  standing: {
    position,
    team: null,
    player: null,
    played: 10,
    won: 5,
    drawn: 2,
    lost: 3,
    points: 17,
    extra: {},
  },
});

const sheet = (
  competitionId: number,
  stats: Record<string, number>,
): PlayerSeasonStats => ({
  competition: comp(competitionId),
  season: "2026/27",
  team: null,
  stats,
});

describe("winner", () => {
  it("respects the direction and ignores ties, gaps and sample sizes", () => {
    expect(winner(metric({}))).toBe("b");
    expect(winner(metric({ better: "lower" }))).toBe("a");
    expect(winner(metric({ a: 2, b: 2 }))).toBeNull();
    expect(winner(metric({ b: null }))).toBeNull();
    expect(winner(metric({ key: "played" }))).toBeNull();
  });
});

describe("formatMetric", () => {
  it("formats by kind", () => {
    expect(formatMetric(metric({ format: "pct" }), 0.456)).toBe("%46");
    expect(formatMetric(metric({ format: "decimal" }), 1.5)).toBe("1.50");
    expect(formatMetric(metric({}), null)).toBe("–");
  });
});

describe("pairing", () => {
  it("finds the shared competition", () => {
    const shared = sharedEntry([entry(1, 4), entry(2, 1)], [entry(2, 3)]);
    expect(shared?.[0].competition.id).toBe(2);
    expect(sharedEntry([entry(1, 1)], [entry(2, 1)])).toBeNull();
  });

  it("prefers sheets from the same competition", () => {
    const [a, b] = pairSheets([sheet(1, {}), sheet(2, {})], [sheet(2, {})]);
    expect(a?.competition.id).toBe(2);
    expect(b?.competition.id).toBe(2);
    expect(pairSheets([], [sheet(5, {})])[1]?.competition.id).toBe(5);
  });
});

describe("playerMetrics", () => {
  it("keeps known keys in order, lower-is-better for finishes", () => {
    const rows = playerMetrics(
      sheet(1, { avg_finish: 3.2, wins: 4, unknown: 1 }),
      sheet(1, { avg_finish: 5.1, wins: 2 }),
      null,
    );
    expect(rows.map((r) => r.key)).toEqual(["wins", "avg_finish"]);
    expect(winner(rows[1])).toBe("a");
  });

  it("starts with league position when both share a table", () => {
    const rows = playerMetrics(null, null, [entry(1, 2), entry(1, 5)]);
    expect(rows[0].key).toBe("position");
    expect(winner(rows[0])).toBe("a");
  });
});

describe("parseCompareType", () => {
  it("defaults to teams", () => {
    expect(parseCompareType("players")).toBe("players");
    expect(parseCompareType("x")).toBe("teams");
    expect(parseCompareType(undefined)).toBe("teams");
  });
});

describe("barShares", () => {
  it("gives the longer bar to the better side", async () => {
    const { barShares } = await import("@/components/compare/compare-parts");
    expect(barShares(metric({ a: 1, b: 3 }))).toEqual([25, 75]);
    expect(barShares(metric({ a: 11, b: 4, better: "lower" }))).toEqual([27, 73]);
    expect(barShares(metric({ a: 0, b: 0 }))).toEqual([0, 0]);
  });
});
