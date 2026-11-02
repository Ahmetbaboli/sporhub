import { describe, expect, it } from "vitest";
import {
  driverPoints,
  driverPositions,
  positionTicks,
  teamProgression,
} from "@/lib/series";
import type { Participant, SportEvent } from "@/lib/types";
import { competition, event, team } from "@/tests/factories";

const arsenal = team(1, "Arsenal FC");
const chelsea = team(2, "Chelsea FC");

function match(id: number, home: number, away: number, extra: Partial<SportEvent> = {}) {
  return event({
    id,
    start_time: `2026-10-${String(id).padStart(2, "0")}T18:00:00Z`,
    participants: [
      {
        team: arsenal,
        player: null,
        side: "home",
        score: home,
        position: null,
        points: null,
        extra: {},
      },
      {
        team: chelsea,
        player: null,
        side: "away",
        score: away,
        position: null,
        points: null,
        extra: {},
      },
    ],
    ...extra,
  });
}

const driver = {
  id: 44,
  name: "Pilot",
  position: "Driver",
  nationality: null,
  team: null,
  extra: {},
};

function race(id: number, position: number, points: number, season = "2026"): SportEvent {
  const result: Participant = {
    team: null,
    player: driver,
    side: null,
    score: null,
    position,
    points,
    extra: {},
  };
  return event({
    id,
    kind: "race",
    name: `GP ${id}`,
    round: String(id),
    season,
    start_time: `2026-0${id}-01T13:00:00Z`,
    participants: [result],
  });
}

describe("teamProgression", () => {
  it("accumulates league points in date order and ignores other competitions", () => {
    const cup = competition({ id: 9, slug: "cup", name: "Cup" });
    const series = teamProgression(
      [
        match(3, 0, 1),
        match(1, 2, 0),
        match(2, 1, 1),
        match(4, 5, 0, { competition: cup }),
      ],
      1,
      true,
    );
    expect(series.map((p) => p.value)).toEqual([3, 4, 4]);
    expect(series[0].label).toContain("CHE");
  });

  it("uses running win percentage without draws", () => {
    const series = teamProgression([match(1, 100, 90), match(2, 80, 99)], 1, false);
    expect(series.map((p) => p.value)).toEqual([100, 50]);
  });

  it("skips unfinished matches", () => {
    expect(teamProgression([match(1, 1, 0, { status: "scheduled" })], 1, true)).toEqual(
      [],
    );
  });
});

describe("driver series", () => {
  const races = [race(2, 3, 15), race(1, 1, 25), race(3, 10, 1)];

  it("lists finishing positions per race", () => {
    expect(driverPositions(races, 44).map((p) => p.value)).toEqual([1, 3, 10]);
  });

  it("accumulates points and keeps only the latest season", () => {
    expect(driverPoints(races, 44).map((p) => p.value)).toEqual([25, 40, 41]);
    expect(driverPoints([race(1, 1, 25, "2025"), race(2, 2, 18)], 44)).toHaveLength(1);
  });
});

describe("positionTicks", () => {
  it("reads as places", () => {
    expect(positionTicks(16)).toEqual([1, 5, 10, 15]);
    expect(positionTicks(3)).toEqual([1]);
  });
});
