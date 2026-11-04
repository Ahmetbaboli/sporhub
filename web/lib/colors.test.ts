import { describe, expect, it } from "vitest";
import { colorDistance, kitPair, readableOn } from "@/lib/colors";

describe("readableOn", () => {
  it("puts black on yellow and white on claret", () => {
    expect(readableOn("#ffff00")).toBe("#000000"); // Fenerbahçe
    expect(readableOn("#aa0031")).toBe("#ffffff"); // Galatasaray
  });
});

describe("kitPair", () => {
  it("keeps both main colours when they differ", () => {
    expect(kitPair({ color: "#ffff00" }, { color: "#aa0031" })).toEqual([
      "#ffff00",
      "#aa0031",
    ]);
  });

  it("switches away to its alternate kit on a clash", () => {
    // Beşiktaş (white) at a white-shirted home side.
    expect(
      kitPair({ color: "#ffffff" }, { color: "#fefefe", alternate_color: "#1a1a1a" }),
    ).toEqual(["#ffffff", "#1a1a1a"]);
  });

  it("gives up rather than guessing when a colour is missing or both kits clash", () => {
    expect(kitPair({ color: null }, { color: "#aa0031" })).toBeNull();
    expect(
      kitPair({ color: "#ffffff" }, { color: "#fafafa", alternate_color: "#f0f0f0" }),
    ).toBeNull();
  });

  it("measures distance in RGB", () => {
    expect(colorDistance("#000000", "#000000")).toBe(0);
    expect(colorDistance("#000000", "bad")).toBe(Infinity);
  });
});
