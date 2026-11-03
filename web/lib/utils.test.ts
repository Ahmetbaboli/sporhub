import { describe, expect, it } from "vitest";
import { badgeCode, cn, initials } from "@/lib/utils";

describe("initials", () => {
  it("uses the first letters of the first two meaningful words", () => {
    expect(initials("Manchester City FC")).toBe("MC");
    expect(initials("Real Madrid CF")).toBe("RM");
  });
  it("falls back to the first two letters for single words", () => {
    expect(initials("Arsenal")).toBe("AR");
  });
  it("skips club prefixes and numbers before falling back", () => {
    expect(initials("FC Lorient")).toBe("LO");
    expect(initials("SV 07 Elversberg")).toBe("EL");
    expect(initials("1. FSV Mainz 05")).toBe("MA");
  });
});

describe("cn", () => {
  it("merges conflicting tailwind classes", () => {
    expect(cn("px-2", false && "hidden", "px-4")).toBe("px-4");
  });
});

describe("badgeCode", () => {
  it("prefers the provider's short code", () => {
    expect(badgeCode({ name: "Galatasaray SK", short_name: "GAL" })).toBe("GAL");
  });
  it("falls back to initials for missing or long short names", () => {
    expect(badgeCode({ name: "Manchester City FC", short_name: "Man City" })).toBe("MC");
    expect(badgeCode({ name: "Arsenal FC" })).toBe("AR");
  });
});
