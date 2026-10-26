import { describe, expect, it } from "vitest";
import {
  groupByDay,
  groupBySportAndCompetition,
  groupSquad,
  positionGroup,
  splitTeamEvents,
} from "@/lib/events";
import type { Player } from "@/lib/types";
import { competition, event } from "@/tests/factories";

describe("groupBySportAndCompetition", () => {
  it("groups by sport then competition, preserving order", () => {
    const pd = competition({ id: 2, slug: "primera-division", name: "Primera Division" });
    const groups = groupBySportAndCompetition([
      event({ id: 1 }),
      event({ id: 2, competition: pd }),
      event({ id: 3 }),
    ]);
    expect(groups).toHaveLength(1);
    expect(groups[0].competitions.map((c) => c.events.map((e) => e.id))).toEqual([
      [1, 3],
      [2],
    ]);
  });
});

describe("groupByDay", () => {
  it("splits events on the Istanbul calendar day", () => {
    const days = groupByDay([
      event({ id: 1, start_time: "2026-10-26T20:30:00Z" }),
      event({ id: 2, start_time: "2026-10-26T21:30:00Z" }), // 00:30 next day in Istanbul
    ]);
    expect(days.map((d) => d.events.length)).toEqual([1, 1]);
  });
});

describe("splitTeamEvents", () => {
  it("returns recent newest-first and upcoming soonest-first", () => {
    const { recent, upcoming } = splitTeamEvents([
      event({ id: 1, start_time: "2026-10-01T12:00:00Z" }),
      event({ id: 2, start_time: "2026-10-08T12:00:00Z" }),
      event({ id: 3, status: "scheduled", start_time: "2026-11-09T12:00:00Z" }),
      event({ id: 4, status: "scheduled", start_time: "2026-11-02T12:00:00Z" }),
    ]);
    expect(recent.map((e) => e.id)).toEqual([2, 1]);
    expect(upcoming.map((e) => e.id)).toEqual([4, 3]);
  });
});

describe("squad grouping", () => {
  const player = (id: number, position: string | null): Player => ({
    id,
    name: `P${id}`,
    position,
    nationality: null,
    team: null,
    extra: {},
  });

  it("maps detailed and coarse positions to groups", () => {
    expect(positionGroup("Goalkeeper")).toBe("goalkeeper");
    expect(positionGroup("Centre-Back")).toBe("defence");
    expect(positionGroup("Central Midfield")).toBe("midfield");
    expect(positionGroup("Offence")).toBe("offence");
    expect(positionGroup(null)).toBe("other");
  });

  it("orders groups and drops empty ones", () => {
    const groups = groupSquad([player(1, "Offence"), player(2, "Goalkeeper")]);
    expect(groups.map((g) => g.group)).toEqual(["goalkeeper", "offence"]);
  });
});
