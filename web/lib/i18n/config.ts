/** Locale settings shared by server and client code (no runtime dependencies). */
export const LOCALES = ["tr", "en"] as const;
export type Locale = (typeof LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "tr";
export const LOCALE_COOKIE = "justsport-locale";
/** One year; the choice is a preference, not a session. */
export const LOCALE_COOKIE_MAX_AGE = 60 * 60 * 24 * 365;

/** BCP 47 tag used for Intl date/number formatting. */
export const INTL_LOCALES: Record<Locale, string> = { tr: "tr-TR", en: "en-GB" };

export function parseLocale(value: string | null | undefined): Locale | null {
  return LOCALES.includes(value as Locale) ? (value as Locale) : null;
}

/** First supported language in an Accept-Language header (q-values in listed order). */
export function localeFromAcceptLanguage(header: string | null | undefined): Locale {
  for (const part of (header ?? "").split(",")) {
    const lang = parseLocale(part.trim().slice(0, 2).toLowerCase());
    if (lang) return lang;
  }
  return DEFAULT_LOCALE;
}
