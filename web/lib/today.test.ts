import { describe, expect, it } from "vitest";
import {
  countByStatus,
  matchesStatus,
  parseTodayState,
  pickFeatured,
  shiftDay,
  todayHref,
  tribuneEvents,
} from "@/lib/today";
import { competition, event } from "@/tests/factories";

const NOW = new Date("2026-11-03T09:00:00Z");

describe("parseTodayState", () => {
  it("keeps a valid date and status, drops junk and today's own date", () => {
    expect(parseTodayState({ date: "2026-11-05", status: "live" }, NOW)).toEqual({
      date: "2026-11-05",
      status: "live",
    });
    expect(parseTodayState({ date: "2026-13-40", status: "evil" }, NOW)).toEqual({
      date: undefined,
      status: "all",
    });
    expect(parseTodayState({ date: "2026-11-03" }, NOW).date).toBeUndefined();
  });
});

describe("date helpers", () => {
  it("shifts calendar days across month ends", () => {
    expect(shiftDay("2026-10-31", 1)).toBe("2026-11-01");
    expect(shiftDay("2026-03-01", -1)).toBe("2026-02-28");
  });
  it("builds links without default values", () => {
    expect(todayHref({ status: "all" })).toBe("/");
    expect(todayHref({ status: "all" }, { status: "finished", date: "2026-01-02" })).toBe(
      "/?date=2026-01-02&status=finished",
    );
  });
});

describe("status filters", () => {
  const events = [
    event({ id: 1, status: "live" }),
    event({ id: 2, status: "scheduled" }),
    event({ id: 3, status: "finished" }),
    event({ id: 4, status: "postponed" }),
  ];
  it("counts each bucket", () => {
    expect(countByStatus(events)).toEqual({ all: 4, live: 1, upcoming: 2, finished: 1 });
    expect(matchesStatus(events[3], "upcoming")).toBe(true);
  });
});

describe("pickFeatured", () => {
  it("puts live games first, then the league order, and skips unlisted leagues", () => {
    const ucl = competition({ id: 2, slug: "uefa-champions-league" });
    const unknown = competition({ id: 3, slug: "regional-cup" });
    const picked = pickFeatured([
      event({ id: 1, status: "scheduled" }),
      event({ id: 2, status: "scheduled", competition: ucl }),
      event({ id: 3, status: "live" }),
      event({ id: 4, status: "live", competition: unknown }),
    ]);
    expect(picked.map((e) => e.id)).toEqual([3, 2, 1]);
  });
});

describe("tribuneEvents", () => {
  it("matches by followed match, league or team", () => {
    const other = event({ id: 9, competition: competition({ id: 7 }), participants: [] });
    const withTeam = event({ id: 5 });
    const homeId = withTeam.participants[0].team!.id;
    expect(
      tribuneEvents([other, withTeam], {
        teams: [homeId],
        competitions: [],
        matches: [],
      }).map((e) => e.id),
    ).toEqual([5]);
    expect(
      tribuneEvents([other], { teams: [], competitions: [], matches: [9] }).map(
        (e) => e.id,
      ),
    ).toEqual([9]);
  });
});
