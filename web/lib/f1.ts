/** Pure helpers for the Formula 1 page (race weekends from Jolpica events). */
import type { Participant, SportEvent, Standing } from "@/lib/types";

export const SESSION_ORDER = [
  "fp1",
  "fp2",
  "fp3",
  "sprint_qualifying",
  "sprint",
  "qualifying",
  "race",
] as const;
export type SessionKey = (typeof SESSION_ORDER)[number];

export interface RaceSession {
  key: SessionKey;
  iso: string;
}

const text = (value: unknown): string | undefined =>
  typeof value === "string" && value ? value : undefined;

export function circuitIdOf(race: SportEvent): string | undefined {
  return text(race.extra.circuit_id);
}

/** "Interlagos" -> place line "São Paulo, Brazil" from the event's own fields. */
export function placeOf(race: SportEvent): string {
  return [text(race.extra.locality), text(race.extra.country)].filter(Boolean).join(", ");
}

/** The circuit name is the venue up to the first comma ("Autódromo José Carlos Pace"). */
export function circuitNameOf(race: SportEvent): string {
  return race.venue?.split(",")[0]?.trim() || race.name || "";
}

/** Weekend sessions in time order, the race itself last (from start_time). */
export function sessionsOf(race: SportEvent): RaceSession[] {
  const raw = (race.extra.sessions ?? {}) as Record<string, unknown>;
  const sessions: RaceSession[] = SESSION_ORDER.filter((k) => k !== "race").flatMap(
    (key) => {
      const iso = text(raw[key]);
      return iso ? [{ key, iso }] : [];
    },
  );
  sessions.push({ key: "race", iso: race.start_time });
  return sessions.sort((a, b) => a.iso.localeCompare(b.iso));
}

/** Next race not yet finished (live counts as next), else undefined. */
export function nextRace(races: SportEvent[]): SportEvent | undefined {
  return races
    .filter((r) => r.status === "scheduled" || r.status === "live")
    .sort((a, b) => a.start_time.localeCompare(b.start_time))[0];
}

export function winnerOf(race: SportEvent): Participant | undefined {
  return race.participants.find((p) => p.position === 1);
}

export function splitChampionship(rows: Standing[]) {
  return {
    drivers: rows.filter((r) => r.player).sort((a, b) => a.position - b.position),
    constructors: rows
      .filter((r) => !r.player && r.team)
      .sort((a, b) => a.position - b.position),
  };
}
