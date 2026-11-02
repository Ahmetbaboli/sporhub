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

const MINUTE = 60;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;
const RELATIVE_LIMIT_DAYS = 7;

/** "2 saat önce" / "2 hours ago" within a week, otherwise a short date. */
export function formatRelative(
  iso: string,
  now: Date = new Date(),
  locale: string = DEFAULT_INTL_LOCALE,
): string {
  const seconds = Math.round((new Date(iso).getTime() - now.getTime()) / 1000);
  const abs = Math.abs(seconds);
  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: "auto" });
  if (abs < HOUR) return rtf.format(Math.round(seconds / MINUTE), "minute");
  if (abs < DAY) return rtf.format(Math.round(seconds / HOUR), "hour");
  if (abs < RELATIVE_LIMIT_DAYS * DAY)
    return rtf.format(Math.round(seconds / DAY), "day");
  return new Intl.DateTimeFormat(locale, {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(iso));
}

/** "2026-10" -> "Ekim 2026" / "October 2026". */
export function formatMonth(month: string, locale: string = DEFAULT_INTL_LOCALE): string {
  return new Intl.DateTimeFormat(locale, {
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${month}-01T00:00:00Z`));
}
