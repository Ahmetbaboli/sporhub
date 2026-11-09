import type { MetadataRoute } from "next";
import { api } from "@/lib/api";
import { absoluteUrl } from "@/lib/site";
import type { Competition, Sport, Team } from "@/lib/types";

// Built per request from our API: at build time the API may not be reachable.
export const dynamic = "force-dynamic";

const TEAMS_LIMIT = 500;
const STATIC_PAGES: { path: string; changeFrequency: "hourly" | "daily" | "monthly" }[] =
  [
    { path: "/", changeFrequency: "hourly" },
    { path: "/news", changeFrequency: "hourly" },
    { path: "/tahmin", changeFrequency: "daily" },
    { path: "/transferler", changeFrequency: "daily" },
    { path: "/compare", changeFrequency: "monthly" },
    { path: "/sources", changeFrequency: "monthly" },
    { path: "/about", changeFrequency: "monthly" },
    { path: "/privacy", changeFrequency: "monthly" },
  ];

async function safely<T>(load: () => Promise<T>, fallback: T): Promise<T> {
  try {
    return await load();
  } catch {
    return fallback; // a sitemap without the API's pages beats a broken sitemap
  }
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const sports = await safely(async () => (await api.sports()).items, [] as Sport[]);
  const [competitions, teams] = await Promise.all([
    Promise.all(
      sports.map((s) =>
        safely(async () => (await api.competitions(s.slug)).items, [] as Competition[]),
      ),
    ),
    safely(async () => (await api.teams({ limit: TEAMS_LIMIT })).items, [] as Team[]),
  ]);
  return [
    ...STATIC_PAGES.map((p) => ({
      url: absoluteUrl(p.path),
      changeFrequency: p.changeFrequency,
    })),
    ...sports.map((s) => ({
      url: absoluteUrl(`/${s.slug}`),
      changeFrequency: "hourly" as const,
    })),
    ...competitions.flat().map((c) => ({
      url: absoluteUrl(`/${c.sport_slug}/${c.slug}`),
      changeFrequency: "hourly" as const,
    })),
    ...teams.map((t) => ({
      url: absoluteUrl(`/teams/${t.id}`),
      changeFrequency: "daily" as const,
    })),
  ];
}
