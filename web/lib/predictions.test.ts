import { beforeEach, describe, expect, it } from "vitest";
import {
  awaitingResult,
  clampGoals,
  finishedScore,
  history,
  isLocked,
  pointsFor,
  type Prediction,
  PREDICTIONS_KEY,
  readPredictions,
  removePrediction,
  savePrediction,
  settle,
  tally,
} from "@/lib/predictions";
import { event } from "@/tests/factories";

const NOW = Date.parse("2026-11-04T12:00:00Z");
const pick = (id: number, home: number, away: number, kickoff: string): Prediction => ({
  eventId: id,
  home,
  away,
  kickoff,
  homeName: "Ev",
  awayName: "Deplasman",
  competition: "Süper Lig",
});

describe("pointsFor", () => {
  it("gives 3 for the exact score, 1 for the right result, else 0", () => {
    expect(pointsFor({ home: 2, away: 1 }, { home: 2, away: 1 })).toBe(3);
    expect(pointsFor({ home: 1, away: 0 }, { home: 3, away: 1 })).toBe(1);
    expect(pointsFor({ home: 1, away: 1 }, { home: 0, away: 0 })).toBe(1);
    expect(pointsFor({ home: 0, away: 2 }, { home: 2, away: 0 })).toBe(0);
  });
});

describe("clampGoals", () => {
  it("accepts whole non-negative numbers and caps silly ones", () => {
    expect(clampGoals("2")).toBe(2);
    expect(clampGoals("")).toBeNull();
    expect(clampGoals("-1")).toBeNull();
    expect(clampGoals("1.5")).toBeNull();
    expect(clampGoals("99")).toBe(20);
  });
});

describe("settling", () => {
  const all = {
    1: pick(1, 2, 1, "2026-11-03T17:00:00Z"), // played
    2: pick(2, 0, 0, "2026-11-03T19:00:00Z"), // played
    3: pick(3, 1, 1, "2026-11-06T19:00:00Z"), // upcoming
  };

  it("asks only for started, unscored matches", () => {
    expect(awaitingResult(all, NOW).sort()).toEqual([1, 2]);
    expect(isLocked("2026-11-06T19:00:00Z", NOW)).toBe(false);
  });

  it("stores the final score and points, leaving the rest alone", () => {
    const next = settle(all, [
      { eventId: 1, home: 2, away: 1 },
      { eventId: 2, home: 3, away: 0 },
    ]);
    expect(next[1].result).toEqual({ home: 2, away: 1, points: 3 });
    expect(next[2].result).toEqual({ home: 3, away: 0, points: 0 });
    expect(next[3].result).toBeUndefined();
    expect(tally(next)).toEqual({
      points: 3,
      settled: 2,
      exact: 1,
      outcome: 0,
      pending: 1,
    });
    expect(awaitingResult(next, NOW)).toEqual([]);
    // Nothing new: the same object, so nothing is written.
    expect(settle(next, [{ eventId: 1, home: 2, away: 1 }])).toBe(next);
  });

  it("lists newest first", () => {
    expect(history(all).map((p) => p.eventId)).toEqual([3, 2, 1]);
  });

  it("reads the final score from a finished event only", () => {
    expect(finishedScore(event())).toEqual({ eventId: 1, home: 2, away: 1 });
    expect(finishedScore(event({ status: "scheduled" }))).toBeNull();
  });
});

describe("storage", () => {
  beforeEach(() => localStorage.clear());

  it("saves, reads back and removes", () => {
    savePrediction(pick(7, 1, 0, "2026-11-06T19:00:00Z"));
    expect(readPredictions()[7]).toMatchObject({ home: 1, away: 0 });
    expect(JSON.parse(localStorage.getItem(PREDICTIONS_KEY)!)[7].home).toBe(1);
    removePrediction(7);
    expect(readPredictions()[7]).toBeUndefined();
  });

  it("survives a corrupted value", () => {
    localStorage.setItem(PREDICTIONS_KEY, "{not json");
    expect(readPredictions()).toEqual({});
  });
});
