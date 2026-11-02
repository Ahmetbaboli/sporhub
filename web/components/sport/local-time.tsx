"use client";

import { useSyncExternalStore } from "react";
import { DEFAULT_TIME_ZONE } from "@/lib/api";
import { formatTime } from "@/lib/format";
import { useIntlLocale } from "@/lib/i18n/client";

const subscribe = () => () => {};

/**
 * Kick-off time. The server (and first client render) uses the default zone so hydration
 * matches; once mounted it switches to the viewer's own time zone.
 */
export function LocalTime({ iso, className }: { iso: string; className?: string }) {
  const zone = useSyncExternalStore(
    subscribe,
    () => Intl.DateTimeFormat().resolvedOptions().timeZone,
    () => DEFAULT_TIME_ZONE,
  );
  const locale = useIntlLocale();
  return (
    <time dateTime={iso} className={className}>
      {formatTime(iso, zone, locale)}
    </time>
  );
}
