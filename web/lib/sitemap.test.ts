import { describe, expect, it, vi } from "vitest";
import { competition } from "@/tests/factories";

vi.mock("@/lib/api", () => ({
  api: {
    sports: vi.fn(async () => ({ items: [{ id: 1, slug: "football", name: "Futbol" }] })),
    competitions: vi.fn(async () => ({ items: [competition({ slug: "super-lig" })] })),
    teams: vi.fn(async () => {
      throw new Error("API down");
    }),
  },
}));

describe("sitemap", () => {
  it("lists static pages, sports and leagues, and survives a failing API call", async () => {
    vi.stubEnv("NEXT_PUBLIC_SITE_URL", "https://js.example");
    const { default: sitemap } = await import("@/app/sitemap");
    const urls = (await sitemap()).map((e) => e.url);
    expect(urls).toContain("https://js.example/");
    expect(urls).toContain("https://js.example/tahmin");
    expect(urls).toContain("https://js.example/football");
    expect(urls).toContain("https://js.example/football/super-lig");
    expect(urls.some((u) => u.includes("/teams/"))).toBe(false); // teams call failed
    vi.unstubAllEnvs();
  });
});
