"use client";

import { useSyncExternalStore } from "react";
import { useT } from "@/lib/i18n/client";

const TICK_MS = 1000;
const SECOND = 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

function subscribe(onTick: () => void) {
  const timer = window.setInterval(onTick, TICK_MS);
  return () => window.clearInterval(timer);
}

/** Split of the time left until `target`, all parts >= 0. */
export function remaining(target: number, now: number) {
  const left = Math.max(0, target - now);
  return {
    done: left === 0,
    days: Math.floor(left / DAY),
    hours: Math.floor((left % DAY) / HOUR),
    minutes: Math.floor((left % HOUR) / MINUTE),
    seconds: Math.floor((left % MINUTE) / SECOND),
  };
}

/**
 * Live countdown to the real race start from the data (`iso`). The server renders nothing
 * time-dependent (no hydration mismatch); the numbers appear once mounted.
 */
export function Countdown({ iso }: { iso: string }) {
  const tr = useT();
  const now = useSyncExternalStore(
    subscribe,
    () => Math.floor(Date.now() / SECOND) * SECOND,
    () => null,
  );
  const target = Date.parse(iso);
  if (now === null) {
    return <div className="h-[3.25rem]" aria-hidden />;
  }
  const left = remaining(target, now);
  if (left.done) {
    return <p className="text-live text-sm font-bold uppercase">{tr.f1.started}</p>;
  }
  const parts = [
    [left.days, tr.f1.units.days],
    [left.hours, tr.f1.units.hours],
    [left.minutes, tr.f1.units.minutes],
    [left.seconds, tr.f1.units.seconds],
  ] as const;
  return (
    <div role="timer" aria-label={tr.f1.countdown} className="flex gap-2">
      {parts.map(([value, unit]) => (
        <div
          key={unit}
          className="bg-muted flex min-w-[3.25rem] flex-col items-center rounded-lg px-2 py-1.5"
        >
          <span className="num text-xl leading-none font-bold">
            {String(value).padStart(2, "0")}
          </span>
          <span className="text-muted-foreground mt-1 text-[10px] font-semibold uppercase">
            {unit}
          </span>
        </div>
      ))}
    </div>
  );
}
