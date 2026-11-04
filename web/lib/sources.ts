/**
 * Display names, links and attribution for the data providers (docs/DATA-SOURCES.md).
 * Keys are the API's source names (`Competition.source`, `/meta` sources).
 */
export interface ProviderInfo {
  name: string;
  url: string;
  /** Attribution wording the provider asks for (shown on /sources and in the footer). */
  attribution: string;
  licence?: { name: string; url: string };
}

export const PROVIDERS: Record<string, ProviderInfo> = {
  "football-data": {
    name: "football-data.org",
    url: "https://www.football-data.org/",
    attribution: "Football data provided by the Football-Data.org API",
  },
  thesportsdb: {
    name: "TheSportsDB",
    url: "https://www.thesportsdb.com/",
    attribution: "Süper Lig ve TFF 1. Lig verisi: TheSportsDB",
  },
  balldontlie: {
    name: "balldontlie",
    url: "https://www.balldontlie.io/",
    attribution: "NBA verisi: balldontlie API",
  },
  espn: {
    name: "ESPN",
    url: "https://www.espn.com/soccer/league/_/name/tur.1",
    attribution: "Süper Lig verisi: ESPN (kişisel, ticari olmayan kullanım)",
  },
  jolpica: {
    name: "Jolpica-F1",
    url: "https://github.com/jolpica/jolpica-f1",
    attribution: "Formula 1 verisi: Jolpica-F1 (Ergast uyumlu)",
    licence: {
      name: "CC BY-NC-SA 4.0",
      url: "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    },
  },
};

export function providerName(source: string | null | undefined): string {
  return (source && PROVIDERS[source]?.name) || source || "";
}

/**
 * Providers whose plan delivers scores late (mirror of the adapters' `scores_delayed`, also
 * exposed by GET /api/v1/meta). A live score from them is labelled "may be delayed".
 */
export const DELAYED_SCORE_SOURCES = new Set(["football-data", "thesportsdb"]);

export function scoreMayBeDelayed(source: string | null | undefined): boolean {
  return Boolean(source && DELAYED_SCORE_SOURCES.has(source));
}
