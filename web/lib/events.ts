import { dayKey } from "@/lib/format";
import { tr } from "@/lib/i18n/tr";
import type { Competition, Participant, Player, SportEvent } from "@/lib/types";

export interface CompetitionGroup {
  competition: Competition;
  events: SportEvent[];
}

export interface SportGroup {
  sportSlug: string;
  competitions: CompetitionGroup[];
}

/** Groups events as sport -> competition, keeping the incoming order stable. */
export function groupBySportAndCompetition(events: SportEvent[]): SportGroup[] {
  const sports = new Map<string, Map<number, CompetitionGroup>>();
  for (const event of events) {
    const comp = event.competition;
    const competitions =
      sports.get(comp.sport_slug) ?? new Map<number, CompetitionGroup>();
    const group = competitions.get(comp.id) ?? { competition: comp, events: [] };
    group.events.push(event);
    competitions.set(comp.id, group);
    sports.set(comp.sport_slug, competitions);
  }
  return [...sports].map(([sportSlug, competitions]) => ({
    sportSlug,
    competitions: [...competitions.values()],
  }));
}

export function groupByDay(
  events: SportEvent[],
): { day: string; events: SportEvent[] }[] {
  const days = new Map<string, SportEvent[]>();
  for (const event of events) {
    const key = dayKey(event.start_time);
    days.set(key, [...(days.get(key) ?? []), event]);
  }
  return [...days].map(([, list]) => ({ day: list[0].start_time, events: list }));
}

export function sideOf(
  event: SportEvent,
  side: "home" | "away",
): Participant | undefined {
  return event.participants.find((p) => p.side === side);
}

export function sportLabel(slug: string): string {
  return (tr.sports as Record<string, string>)[slug] ?? slug;
}

/** Splits a team's events into recent results (newest first) and upcoming (soonest first). */
export function splitTeamEvents(events: SportEvent[], limit = 5) {
  const byTime = (a: SportEvent, b: SportEvent) =>
    a.start_time.localeCompare(b.start_time);
  const recent = events
    .filter((e) => e.status === "finished")
    .sort((a, b) => byTime(b, a))
    .slice(0, limit);
  const upcoming = events
    .filter((e) => e.status === "scheduled" || e.status === "live")
    .sort(byTime)
    .slice(0, limit);
  return { recent, upcoming };
}

export type PositionGroup = keyof typeof tr.team.positions;

export function positionGroup(position: string | null): PositionGroup {
  const p = (position ?? "").toLowerCase();
  if (p.includes("goalkeeper")) return "goalkeeper";
  if (p.includes("back") || p.includes("defence")) return "defence";
  if (p.includes("midfield")) return "midfield";
  if (p.includes("winger") || p.includes("forward") || p.includes("offence"))
    return "offence";
  return "other";
}

const POSITION_ORDER: PositionGroup[] = [
  "goalkeeper",
  "defence",
  "midfield",
  "offence",
  "other",
];

export function groupSquad(
  squad: Player[],
): { group: PositionGroup; players: Player[] }[] {
  return POSITION_ORDER.map((group) => ({
    group,
    players: squad.filter((p) => positionGroup(p.position) === group),
  })).filter((g) => g.players.length > 0);
}
