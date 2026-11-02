import { describe, expect, it } from "vitest";
import { PALETTE_BOOT_SCRIPT, PALETTES, parsePalette } from "@/lib/palettes";

describe("palettes", () => {
  it("falls back to the default for unknown values", () => {
    expect(parsePalette("ocean")).toBe("ocean");
    expect(parsePalette("<script>")).toBe("pitch");
    expect(parsePalette(null)).toBe("pitch");
  });

  it("boot script applies only known, non-default palettes", () => {
    for (const [stored, expected] of [
      ["violet", "violet"],
      ["pitch", undefined],
      ["evil", undefined],
    ] as const) {
      localStorage.setItem("justsport-palette", stored);
      delete document.documentElement.dataset.palette;
      new Function(PALETTE_BOOT_SCRIPT)();
      expect(document.documentElement.dataset.palette).toBe(expected);
    }
    expect(PALETTES[0]).toBe("pitch");
  });
});
