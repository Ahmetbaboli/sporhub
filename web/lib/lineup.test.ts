import { describe, expect, it } from "vitest";
import { formationLines, pitchName } from "@/lib/lineup";
import type { Lineup } from "@/lib/types";

function lineup(formation: string, positions: string[]): Lineup {
  return {
    side: "home",
    formation,
    starters: positions.map((position, i) => ({
      external_id: String(i),
      name: position,
      number: String(i + 1),
      position,
      subbed_in: false,
      subbed_out: false,
    })),
    substitutes: [],
  };
}

const names = (lines: ReturnType<typeof formationLines>) =>
  lines?.map((line) => line.map((p) => p.name));

describe("formationLines", () => {
  it("splits a real ESPN 4-2-3-1 into lines, left to right", () => {
    // Fenerbahçe v Göztepe, 2026-10-31, in the provider's formation-place order.
    const fb = lineup("4-2-3-1", [
      "G",
      "CD-L",
      "CD-R",
      "LB",
      "RB",
      "AM",
      "LM",
      "RM",
      "F",
      "AM-L",
      "AM-R",
    ]);
    expect(names(formationLines(fb))).toEqual([
      ["G"],
      ["LB", "CD-L", "CD-R", "RB"],
      ["LM", "RM"],
      ["AM-L", "AM", "AM-R"],
      ["F"],
    ]);
  });

  it("splits a real ESPN 3-4-1-2", () => {
    const goz = lineup("3-4-1-2", [
      "G",
      "CD",
      "CD-L",
      "CD-R",
      "CM-L",
      "CM-R",
      "AM",
      "LM",
      "RM",
      "CF-L",
      "CF-R",
    ]);
    expect(names(formationLines(goz))).toEqual([
      ["G"],
      ["CD-L", "CD", "CD-R"],
      ["LM", "CM-L", "CM-R", "RM"],
      ["AM"],
      ["CF-L", "CF-R"],
    ]);
  });

  it("gives up (list view) when the numbers do not add up", () => {
    expect(formationLines(lineup("4-4-2", ["G", "CD"]))).toBeNull();
    expect(formationLines({ ...lineup("4-4-2", []), formation: null })).toBeNull();
  });
});

describe("pitchName", () => {
  it("keeps the surname only", () => {
    expect(pitchName("Matteo Guendouzi")).toBe("Guendouzi");
    expect(pitchName("Ederson")).toBe("Ederson");
  });
});
