/** Chart series derived from event lists (pure, so they are unit-tested without a DOM). */
import type { SportEvent } from "@/lib/types";

export interface SeriesPoint {
  /** Short x-axis label (round number / match number). */
  x: string;
  /** Long label for tooltips and the table view. */
  label: string;
  value: number;
}

const WIN_POINTS = 3;
const DRAW_POINTS = 1;
const PERCENT = 100;

function byStart(a: SportEvent, b: SportEvent): number {
  return a.start_time.localeCompare(b.start_time);
}

function finished(events: SportEvent[], kind: SportEvent["kind"]): SportEvent[] {
  return events.filter((e) => e.kind === kind && e.status === "finished").sort(byStart);
}

/** One driver's finishing position per finished race of the latest season. */
export function driverPositions(events: SportEvent[], playerId: number): SeriesPoint[] {
  return latestSeason(finished(events, "race")).flatMap((e) => {
    const mine = e.participants.find((p) => p.player?.id === playerId);
    if (!mine?.position) return [];
    return [{ x: e.round ?? "", label: e.name ?? e.round ?? "", value: mine.position }];
  });
}

/** Cumulative Grand Prix points after each race of the latest season. */
export function driverPoints(events: SportEvent[], playerId: number): SeriesPoint[] {
  let total = 0;
  return latestSeason(finished(events, "race")).flatMap((e) => {
    const mine = e.participants.find((p) => p.player?.id === playerId);
    if (!mine) return [];
    total += mine.points ?? 0;
    return [{ x: e.round ?? "", label: e.name ?? e.round ?? "", value: total }];
  });
}

function latestSeason(events: SportEvent[]): SportEvent[] {
  const last = events.at(-1)?.season;
  return last ? events.filter((e) => e.season === last) : [];
}

/** The competition in which the team played most finished matches (its league). */
function mainCompetition(matches: SportEvent[]): SportEvent[] {
  const counts = new Map<number, number>();
  for (const m of matches) {
    counts.set(m.competition.id, (counts.get(m.competition.id) ?? 0) + 1);
  }
  const [best] = [...counts].sort((a, b) => b[1] - a[1])[0] ?? [];
  return matches.filter((m) => m.competition.id === best);
}

function outcome(event: SportEvent, teamId: number): "W" | "D" | "L" | null {
  const mine = event.participants.find((p) => p.team?.id === teamId);
  const other = event.participants.find((p) => p.team && p.team.id !== teamId);
  if (mine?.score == null || other?.score == null) return null;
  return mine.score > other.score ? "W" : mine.score < other.score ? "L" : "D";
}

function opponentName(event: SportEvent, teamId: number): string {
  const other = event.participants.find((p) => p.team && p.team.id !== teamId)?.team;
  return other?.short_name ?? other?.name ?? "";
}

/**
 * League progression: cumulative points (3/1/0) when draws exist, otherwise the running
 * win percentage. Only the latest season of the team's main competition is used.
 */
export function teamProgression(
  events: SportEvent[],
  teamId: number,
  draws: boolean,
): SeriesPoint[] {
  const matches = mainCompetition(latestSeason(finished(events, "match")));
  let points = 0;
  let wins = 0;
  let played = 0;
  return matches.flatMap((e) => {
    const result = outcome(e, teamId);
    if (!result) return [];
    played += 1;
    wins += result === "W" ? 1 : 0;
    points += result === "W" ? WIN_POINTS : result === "D" ? DRAW_POINTS : 0;
    const value = draws ? points : Math.round((wins / played) * PERCENT);
    return [{ x: String(played), label: `${played}. ${opponentName(e, teamId)}`, value }];
  });
}

const POSITION_TICK_STEP = 5;

/** 1, 5, 10, 15... up to the worst position, so the axis reads as places. */
export function positionTicks(max: number): number[] {
  const ticks = [1];
  for (let t = POSITION_TICK_STEP; t <= max; t += POSITION_TICK_STEP) ticks.push(t);
  return ticks;
}
