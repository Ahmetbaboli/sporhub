import { Flag, Goal, CircleDot, Trophy, type LucideIcon } from "lucide-react";
import type { Messages } from "@/lib/i18n/tr";

/**
 * Per-sport presentation rules. The API returns the same shapes for every sport; this table
 * is the single place that decides how a sport is *shown* (tab names, standings layout, icon).
 * Adding a sport to the UI = add a row here (see docs/adding-a-sport.md).
 */
export type StandingsLayout = "league" | "conference" | "championship";

export interface SportTemplate {
  icon: LucideIcon;
  standings: StandingsLayout;
  /** Tab labels picked from the active language's messages (resolved at render time). */
  tabs: (m: Messages) => Messages["competition"]["tabs"];
  /** Events per page on the fixtures/results tabs (race cards are tall, so fewer). */
  pageSize: number;
  /** How team form/analysis is shown; null = sport has no two-sided matches (races). */
  analysis: { draws: boolean; cleanSheets: boolean; unit: "goals" | "points" } | null;
}

const DEFAULT_TEMPLATE: SportTemplate = {
  icon: Trophy,
  standings: "league",
  tabs: (m) => m.competition.tabs,
  pageSize: 20,
  analysis: { draws: true, cleanSheets: true, unit: "goals" },
};

const TEMPLATES: Record<string, SportTemplate> = {
  football: { ...DEFAULT_TEMPLATE, icon: Goal },
  basketball: {
    icon: CircleDot,
    standings: "conference",
    tabs: (m) => m.competition.tabsBySport.basketball,
    pageSize: 20,
    analysis: { draws: false, cleanSheets: false, unit: "points" },
  },
  "formula-1": {
    icon: Flag,
    standings: "championship",
    tabs: (m) => m.competition.tabsBySport["formula-1"],
    pageSize: 6,
    analysis: null,
  },
};

export function templateFor(sportSlug: string): SportTemplate {
  return TEMPLATES[sportSlug] ?? DEFAULT_TEMPLATE;
}
