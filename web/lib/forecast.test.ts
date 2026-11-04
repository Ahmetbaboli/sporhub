import { describe, expect, it } from "vitest";
import { formatChance, likelyRange } from "@/lib/forecast";

describe("formatChance", () => {
  it("writes Turkish and English percentages, with edges spelled out", () => {
    expect(formatChance(0.53, "tr-TR")).toBe("%53");
    expect(formatChance(0.53, "en-GB")).toBe("53%");
    expect(formatChance(0, "tr-TR")).toBe("–");
    expect(formatChance(0.001, "tr-TR")).toBe("<%1");
    expect(formatChance(0.998, "tr-TR")).toBe(">%99");
    expect(formatChance(1, "tr-TR")).toBe("%100");
  });
});

describe("likelyRange", () => {
  it("grows around the most likely place until most runs are covered", () => {
    expect(likelyRange([0.9, 0.1, 0])).toEqual([1, 1]);
    expect(likelyRange([0.05, 0.4, 0.35, 0.15, 0.05])).toEqual([2, 4]);
    expect(likelyRange([0, 0, 1])).toEqual([3, 3]);
  });
});
