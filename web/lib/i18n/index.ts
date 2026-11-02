/**
 * Request-scoped translations for server components.
 *
 * Every page/layout/metadata entry point awaits `initLocale()` once; after that any server
 * component in its tree (sync or async) reads strings with `t()`. React's `cache` scopes the
 * store to one request, so concurrent requests never see each other's language. Outside a
 * request (unit tests) the default language is used. Client components use `useT()`.
 */
import { cache } from "react";
import {
  DEFAULT_LOCALE,
  INTL_LOCALES,
  LOCALE_COOKIE,
  type Locale,
  localeFromAcceptLanguage,
  parseLocale,
} from "@/lib/i18n/config";
import { en } from "@/lib/i18n/en";
import { type Messages, tr } from "@/lib/i18n/tr";

export const MESSAGES: Record<Locale, Messages> = { tr, en };

const store = cache((): { locale: Locale } => ({ locale: DEFAULT_LOCALE }));

/** Reads the visitor's language (cookie, then Accept-Language) into the request store. */
export async function initLocale(): Promise<Locale> {
  const { cookies, headers } = await import("next/headers");
  const fromCookie = parseLocale((await cookies()).get(LOCALE_COOKIE)?.value);
  const locale =
    fromCookie ?? localeFromAcceptLanguage((await headers()).get("accept-language"));
  store().locale = locale;
  return locale;
}

export function getLocale(): Locale {
  return store().locale;
}

export function t(): Messages {
  return MESSAGES[getLocale()];
}

export function intlLocale(): string {
  return INTL_LOCALES[getLocale()];
}
