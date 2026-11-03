import { describe, expect, it } from "vitest";
import {
  emptyTribune,
  isTribuneEmpty,
  parseTribune,
  prioritize,
  serializeTribune,
  toggleInTribune,
} from "@/lib/tribune";

describe("tribune cookie", () => {
  it("round-trips ids per kind", () => {
    const tribune = { teams: [3, 1], competitions: [7], players: [], matches: [42] };
    expect(serializeTribune(tribune)).toBe("t:3.1|c:7|m:42");
    expect(parseTribune(serializeTribune(tribune))).toEqual(tribune);
  });

  it("ignores malformed parts instead of throwing", () => {
    expect(parseTribune("t:1.x.1.-2|zz:9|c:")).toEqual({ ...emptyTribune(), teams: [1] });
    expect(isTribuneEmpty(parseTribune(undefined))).toBe(true);
  });

  it("toggles newest first", () => {
    const once = toggleInTribune(emptyTribune(), "teams", 5);
    const twice = toggleInTribune(once, "teams", 8);
    expect(twice.teams).toEqual([8, 5]);
    expect(toggleInTribune(twice, "teams", 5).teams).toEqual([8]);
  });
});

describe("prioritize", () => {
  it("moves favourites to the front in favourite order and keeps the rest stable", () => {
    const items = [{ id: 1 }, { id: 2 }, { id: 3 }, { id: 4 }];
    expect(prioritize(items, [3, 1], (i) => [i.id]).map((i) => i.id)).toEqual([
      3, 1, 2, 4,
    ]);
  });
});
