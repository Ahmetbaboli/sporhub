import { afterEach, describe, expect, it, vi } from "vitest";
import robots from "@/app/robots";
import { shareMetadata } from "@/lib/share";
import { absoluteUrl, siteUrl } from "@/lib/site";

describe("siteUrl", () => {
  afterEach(() => vi.unstubAllEnvs());

  it("prefers the configured address, then Vercel's domain, then localhost", () => {
    vi.stubEnv("NEXT_PUBLIC_SITE_URL", "https://js.example/");
    expect(siteUrl()).toBe("https://js.example");
    vi.stubEnv("NEXT_PUBLIC_SITE_URL", "");
    vi.stubEnv("VERCEL_PROJECT_PRODUCTION_URL", "justsport.vercel.app");
    expect(siteUrl()).toBe("https://justsport.vercel.app");
    vi.stubEnv("VERCEL_PROJECT_PRODUCTION_URL", "");
    expect(absoluteUrl("tahmin")).toBe("http://localhost:3000/tahmin");
  });
});

describe("robots", () => {
  it("keeps personal pages out and points at the sitemap", () => {
    vi.stubEnv("NEXT_PUBLIC_SITE_URL", "https://js.example");
    const r = robots();
    expect(r.sitemap).toBe("https://js.example/sitemap.xml");
    const rule = Array.isArray(r.rules) ? r.rules[0] : r.rules;
    expect(rule.disallow).toEqual(expect.arrayContaining(["/admin", "/me", "/api/"]));
    vi.unstubAllEnvs();
  });
});

describe("shareMetadata", () => {
  it("fills the share card text and asks for the large card", () => {
    const m = shareMetadata("Galatasaray SK", "Fikstür ve form.");
    expect(m.title).toBe("Galatasaray SK");
    expect(m.openGraph).toMatchObject({
      title: "Galatasaray SK · Just Sport",
      description: "Fikstür ve form.",
      siteName: "Just Sport",
    });
    expect(m.twitter).toMatchObject({ card: "summary_large_image" });
  });
});
