"use client";

import { useSyncExternalStore } from "react";
import { DEFAULT_TIME_ZONE } from "@/lib/api";
import { useIntlLocale } from "@/lib/i18n/client";

const subscribe = () => () => {};

/**
 * "Cmt 7 Kas 21:00" in the viewer's time zone (server and first render use the default zone
 * so hydration matches, like LocalTime).
 */
export function LocalDateTime({
  iso,
  className,
  withWeekday = true,
}: {
  iso: string;
  className?: string;
  withWeekday?: boolean;
}) {
  const zone = useSyncExternalStore(
    subscribe,
    () => Intl.DateTimeFormat().resolvedOptions().timeZone,
    () => DEFAULT_TIME_ZONE,
  );
  const locale = useIntlLocale();
  const text = new Intl.DateTimeFormat(locale, {
    weekday: withWeekday ? "short" : undefined,
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: zone,
  }).format(new Date(iso));
  return (
    <time dateTime={iso} className={className}>
      {text}
    </time>
  );
}
