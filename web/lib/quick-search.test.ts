import { describe, expect, it } from "vitest";
import {
  flattenResults,
  isOpenShortcut,
  QUICK_GROUP_LIMIT,
  searchPageHref,
} from "@/lib/quick-search";
import type { Player } from "@/lib/types";
import { competition, team } from "@/tests/factories";

const player = (id: number): Player => ({
  id,
  name: `Oyuncu ${id}`,
  position: "Forvet",
  nationality: null,
  team: team(1, "Galatasaray SK"),
  extra: {},
});

describe("flattenResults", () => {
  it("lists teams, leagues, players, then the full results link", () => {
    const items = flattenResults(
      {
        query: "gal",
        competitions: [competition()],
        teams: [team(1, "Galatasaray SK")],
        players: [player(7)],
      },
      " gal ",
    );
    expect(items.map((i) => i.kind)).toEqual(["team", "competition", "player", "all"]);
    expect(items[0].href).toBe("/teams/1");
    expect(items[2]).toMatchObject({
      href: "/players/7",
      subtitle: "Forvet · Galatasaray SK",
    });
    expect(items[3].href).toBe("/search?q=gal");
  });

  it("keeps the list short", () => {
    const teams = Array.from({ length: 12 }, (_, i) => team(i + 1, `Takım ${i}`));
    const items = flattenResults(
      { query: "t", competitions: [], teams, players: [] },
      "ta",
    );
    expect(items.filter((i) => i.kind === "team")).toHaveLength(QUICK_GROUP_LIMIT);
  });
});

describe("isOpenShortcut", () => {
  const body = document.body;
  const input = document.createElement("input");
  const key = (
    k: string,
    mods: Partial<KeyboardEvent> = {},
    target: EventTarget = body,
  ) => ({
    key: k,
    ctrlKey: false,
    metaKey: false,
    altKey: false,
    ...mods,
    target,
  });

  it("opens on Ctrl+K and ⌘K, even while typing", () => {
    expect(isOpenShortcut(key("k", { ctrlKey: true }))).toBe(true);
    expect(isOpenShortcut(key("K", { metaKey: true }, input))).toBe(true);
    expect(isOpenShortcut(key("k"))).toBe(false);
    expect(isOpenShortcut(key("k", { ctrlKey: true, altKey: true }))).toBe(false);
  });

  it('opens on "/" only outside text fields', () => {
    expect(isOpenShortcut(key("/"))).toBe(true);
    expect(isOpenShortcut(key("/", {}, input))).toBe(false);
  });
});

describe("searchPageHref", () => {
  it("encodes Turkish letters and spaces", () => {
    expect(searchPageHref(" Beşiktaş JK ")).toBe("/search?q=Be%C5%9Fikta%C5%9F%20JK");
  });
});
