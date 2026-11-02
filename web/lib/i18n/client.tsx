"use client";

import { createContext, useContext } from "react";
import { DEFAULT_LOCALE, INTL_LOCALES, type Locale } from "@/lib/i18n/config";
import { en } from "@/lib/i18n/en";
import { type Messages, tr } from "@/lib/i18n/tr";

const MESSAGES: Record<Locale, Messages> = { tr, en };
const LocaleContext = createContext<Locale>(DEFAULT_LOCALE);

/** The root layout passes the request's locale down to client components. */
export function I18nProvider({
  locale,
  children,
}: {
  locale: Locale;
  children: React.ReactNode;
}) {
  return <LocaleContext.Provider value={locale}>{children}</LocaleContext.Provider>;
}

export function useLocale(): Locale {
  return useContext(LocaleContext);
}

export function useT(): Messages {
  return MESSAGES[useLocale()];
}

export function useIntlLocale(): string {
  return INTL_LOCALES[useLocale()];
}
