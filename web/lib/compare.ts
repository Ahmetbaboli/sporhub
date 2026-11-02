/**
 * Side-by-side comparison rows. Pure functions: the /compare page renders whatever these
 * return, so the "who is better" rules live (and are tested) here.
 */
import { t } from "@/lib/i18n";
import type { SportTemplate } from "@/lib/sports";
import type { PlayerSeasonStats, StandingEntry, TeamAnalysis } from "@/lib/types";

export type CompareType = "teams" | "players";
export type Better = "higher" | "lower";

export interface CompareMetric {
  key: string;
  label: string;
  a: number | null;
  b: number | null;
  better: Better;
  format: "int" | "decimal" | "pct";
}

const PERCENT = 100;

/** Stat-sheet keys in display order; anything else is ignored. */
const PLAYER_KEYS = [
  "played",
  "goals",
  "assists",
  "goals_per_match",
  "penalties",
  "races",
  "race_points",
  "wins",
  "podiums",
  "poles",
  "fastest_laps",
  "best_finish",
  "avg_finish",
  "dnf",
] as const;
const LOWER_IS_BETTER = new Set(["best_finish", "avg_finish", "dnf"]);
const DECIMAL_KEYS = new Set(["goals_per_match", "avg_finish"]);
/** Sample sizes are context, not something to "win". */
const NEUTRAL_KEYS = new Set(["played", "races"]);

export function parseCompareType(value: string | undefined): CompareType {
  return value === "players" ? "players" : "teams";
}

export function winner(metric: CompareMetric): "a" | "b" | null {
  const { a, b } = metric;
  if (a === null || b === null || a === b || NEUTRAL_KEYS.has(metric.key)) return null;
  const aWins = metric.better === "higher" ? a > b : a < b;
  return aWins ? "a" : "b";
}

export function formatMetric(metric: CompareMetric, value: number | null): string {
  if (value === null) return "–";
  if (metric.format === "pct") return `%${Math.round(value * PERCENT)}`;
  if (metric.format === "decimal") return value.toFixed(2);
  return String(Math.round(value));
}

/** The first competition both appear in (same table), so positions are comparable. */
export function sharedEntry(
  a: StandingEntry[],
  b: StandingEntry[],
): [StandingEntry, StandingEntry] | null {
  for (const entry of a) {
    const other = b.find((e) => e.competition.id === entry.competition.id);
    if (other) return [entry, other];
  }
  return null;
}

function standingMetrics(shared: [StandingEntry, StandingEntry] | null): CompareMetric[] {
  if (!shared) return [];
  const [a, b] = shared;
  return [
    {
      key: "position",
      label: `${t().compare.leaguePosition} · ${a.competition.name}`,
      a: a.standing.position,
      b: b.standing.position,
      better: "lower",
      format: "int",
    },
    {
      key: "points",
      label: t().compare.leaguePoints,
      a: a.standing.points,
      b: b.standing.points,
      better: "higher",
      format: "int",
    },
  ];
}

export function teamMetrics(
  a: TeamAnalysis | null,
  b: TeamAnalysis | null,
  shared: [StandingEntry, StandingEntry] | null,
  rules: SportTemplate["analysis"],
): CompareMetric[] {
  const metrics = standingMetrics(shared);
  if (!rules || !a || !b || (a.overall.played === 0 && b.overall.played === 0)) {
    return metrics;
  }
  const unit = rules.unit;
  const row = (
    key: string,
    label: string,
    pick: (t: TeamAnalysis) => number,
    better: Better,
    format: CompareMetric["format"],
  ): CompareMetric => ({ key, label, a: pick(a), b: pick(b), better, format });
  metrics.push(
    row("played", t().analysis.played, (t) => t.overall.played, "higher", "int"),
    row("win_pct", t().analysis.winPct, (t) => t.overall.win_pct, "higher", "pct"),
    row(
      "avg_scored",
      t().analysis.avgScored[unit],
      (t) => t.overall.avg_scored,
      "higher",
      "decimal",
    ),
    row(
      "avg_conceded",
      t().analysis.avgConceded[unit],
      (t) => t.overall.avg_conceded,
      "lower",
      "decimal",
    ),
  );
  if (rules.cleanSheets) {
    metrics.push(
      row(
        "clean_sheets",
        t().analysis.cleanSheets,
        (t) => t.overall.clean_sheets,
        "higher",
        "int",
      ),
    );
  }
  metrics.push(
    row(
      "home_win_pct",
      `${t().analysis.home} · ${t().analysis.winPct}`,
      (t) => t.home.win_pct,
      "higher",
      "pct",
    ),
    row(
      "away_win_pct",
      `${t().analysis.away} · ${t().analysis.winPct}`,
      (t) => t.away.win_pct,
      "higher",
      "pct",
    ),
  );
  return metrics;
}

/** Picks the sheets to compare: the same competition when both have one, else each one's first. */
export function pairSheets(
  a: PlayerSeasonStats[],
  b: PlayerSeasonStats[],
): [PlayerSeasonStats | null, PlayerSeasonStats | null] {
  for (const sheet of a) {
    const other = b.find((s) => s.competition.id === sheet.competition.id);
    if (other) return [sheet, other];
  }
  return [a[0] ?? null, b[0] ?? null];
}

export function playerMetrics(
  a: PlayerSeasonStats | null,
  b: PlayerSeasonStats | null,
  shared: [StandingEntry, StandingEntry] | null,
): CompareMetric[] {
  const metrics = standingMetrics(shared);
  const labels = t().compare.metrics as Record<string, string>;
  for (const key of PLAYER_KEYS) {
    const va = a?.stats[key];
    const vb = b?.stats[key];
    if (va === undefined && vb === undefined) continue;
    metrics.push({
      key,
      label: labels[key] ?? key,
      a: va ?? null,
      b: vb ?? null,
      better: LOWER_IS_BETTER.has(key) ? "lower" : "higher",
      format: DECIMAL_KEYS.has(key) ? "decimal" : "int",
    });
  }
  return metrics;
}
