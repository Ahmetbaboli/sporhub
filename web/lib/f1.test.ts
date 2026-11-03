import { describe, expect, it } from "vitest";
import { remaining } from "@/components/f1/countdown";
import { CIRCUITS } from "@/lib/circuits";
import { circuitNameOf, nextRace, placeOf, sessionsOf } from "@/lib/f1";
import { event } from "@/tests/factories";

const race = event({
  id: 20,
  kind: "race",
  name: "Brazilian Grand Prix",
  status: "scheduled",
  start_time: "2026-11-08T17:00:00Z",
  venue: "Autódromo José Carlos Pace, São Paulo, Brazil",
  participants: [],
  extra: {
    circuit_id: "interlagos",
    locality: "São Paulo",
    country: "Brazil",
    sessions: {
      qualifying: "2026-11-07T18:00:00Z",
      fp1: "2026-11-06T14:30:00Z",
      sprint: "2026-11-07T14:00:00Z",
    },
  },
});

describe("F1 helpers", () => {
  it("orders the weekend by time with the race last", () => {
    expect(sessionsOf(race).map((s) => s.key)).toEqual([
      "fp1",
      "sprint",
      "qualifying",
      "race",
    ]);
  });

  it("reads place and circuit from the event's own fields", () => {
    expect(placeOf(race)).toBe("São Paulo, Brazil");
    expect(circuitNameOf(race)).toBe("Autódromo José Carlos Pace");
  });

  it("picks the earliest race that is not finished", () => {
    const done = {
      ...race,
      id: 19,
      status: "finished" as const,
      start_time: "2026-11-01T20:00:00Z",
    };
    const later = { ...race, id: 21, start_time: "2026-11-22T04:00:00Z" };
    expect(nextRace([later, done, race])?.id).toBe(20);
  });

  it("has an outline for the circuit ids on the 2026 calendar", () => {
    for (const id of ["interlagos", "vegas", "losail", "yas_marina", "madring"]) {
      expect(CIRCUITS[id]?.path).toMatch(/^M[\d.]+ [\d.]+L.*Z$/);
    }
  });
});

describe("countdown", () => {
  it("splits the time left and never goes negative", () => {
    const now = Date.parse("2026-11-03T10:00:00Z");
    expect(remaining(Date.parse("2026-11-05T13:04:05Z"), now)).toEqual({
      done: false,
      days: 2,
      hours: 3,
      minutes: 4,
      seconds: 5,
    });
    expect(remaining(now - 1, now).done).toBe(true);
  });
});
