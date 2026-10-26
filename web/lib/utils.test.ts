import { describe, expect, it } from "vitest";
import { cn, initials } from "@/lib/utils";

describe("initials", () => {
  it("uses the first letters of the first two meaningful words", () => {
    expect(initials("Manchester City FC")).toBe("MC");
    expect(initials("Real Madrid CF")).toBe("RM");
  });
  it("falls back to the first two letters for single words", () => {
    expect(initials("Arsenal")).toBe("AR");
  });
});

describe("cn", () => {
  it("merges conflicting tailwind classes", () => {
    expect(cn("px-2", false && "hidden", "px-4")).toBe("px-4");
  });
});
