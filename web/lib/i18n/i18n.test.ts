import { describe, expect, it } from "vitest";
import { localeFromAcceptLanguage, parseLocale } from "@/lib/i18n/config";
import { en } from "@/lib/i18n/en";
import { getLocale, t } from "@/lib/i18n";
import { tr } from "@/lib/i18n/tr";

/** Every leaf as [path, value]; functions are called with sample arguments. */
function leaves(node: unknown, path = ""): [string, string][] {
  if (typeof node === "string") return [[path, node]];
  if (typeof node === "function") return [[path, String(node(2, 1, 0))]];
  return Object.entries(node as object).flatMap(([k, v]) => leaves(v, `${path}.${k}`));
}

describe("locale selection", () => {
  it("accepts only supported locales", () => {
    expect(parseLocale("en")).toBe("en");
    expect(parseLocale("de")).toBeNull();
    expect(parseLocale(undefined)).toBeNull();
  });

  it("reads Accept-Language in order, defaulting to Turkish", () => {
    expect(localeFromAcceptLanguage("en-US,en;q=0.9,tr;q=0.8")).toBe("en");
    expect(localeFromAcceptLanguage("de-DE,tr;q=0.8")).toBe("tr");
    expect(localeFromAcceptLanguage("fr")).toBe("tr");
    expect(localeFromAcceptLanguage(null)).toBe("tr");
  });

  it("uses Turkish outside a request", () => {
    expect(getLocale()).toBe("tr");
    expect(t().nav.home).toBe("Bugün");
  });
});

describe("dictionaries", () => {
  it("have the same keys and no empty strings", () => {
    const trLeaves = leaves(tr);
    const enLeaves = leaves(en);
    expect(enLeaves.map(([p]) => p)).toEqual(trLeaves.map(([p]) => p));
    for (const [path, value] of enLeaves) expect(value, path).not.toBe("");
  });

  it("translates the visible basics", () => {
    expect(en.nav.home).toBe("Today");
    expect(en.analysis.winLoss(3, 2)).toBe("3W · 2L");
  });
});
