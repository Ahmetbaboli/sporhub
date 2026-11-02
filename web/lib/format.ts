import { DEFAULT_TIME_ZONE } from "@/lib/api";

const DEFAULT_INTL_LOCALE = "tr-TR";

export function formatTime(
  iso: string,
  timeZone: string = DEFAULT_TIME_ZONE,
  locale: string = DEFAULT_INTL_LOCALE,
): string {
  return new Intl.DateTimeFormat(locale, {
    hour: "2-digit",
    minute: "2-digit",
    timeZone,
  }).format(new Date(iso));
}

export function formatDay(
  iso: string,
  timeZone: string = DEFAULT_TIME_ZONE,
  locale: string = DEFAULT_INTL_LOCALE,
): string {
  return new Intl.DateTimeFormat(locale, {
    weekday: "long",
    day: "numeric",
    month: "long",
    timeZone,
  }).format(new Date(iso));
}

/** Calendar-day key (YYYY-MM-DD) in a time zone, for grouping events by day. */
export function dayKey(iso: string, timeZone: string = DEFAULT_TIME_ZONE): string {
  return new Intl.DateTimeFormat("sv-SE", { timeZone }).format(new Date(iso));
}

export function formatDate(
  isoDate: string,
  locale: string = DEFAULT_INTL_LOCALE,
): string {
  return new Intl.DateTimeFormat(locale, {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(isoDate));
}
