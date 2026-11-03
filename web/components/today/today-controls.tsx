import { CalendarDays, ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { t } from "@/lib/i18n";
import {
  shiftDay,
  STATUS_FILTERS,
  type StatusFilter,
  type TodayState,
  todayHref,
  todayKey,
} from "@/lib/today";
import { cn } from "@/lib/utils";

const ICON_BUTTON =
  "bg-card hover:bg-muted inline-flex size-10 items-center justify-center rounded-md border transition-colors duration-150";

/** Previous / pick / next day. Works without JavaScript (plain links and a GET form). */
export function DatePicker({ state }: { state: TodayState }) {
  const day = state.date ?? todayKey();
  const isToday = !state.date;
  return (
    <div className="flex items-center gap-1.5">
      <Link
        href={todayHref(state, { date: shiftDay(day, -1) })}
        className={ICON_BUTTON}
        aria-label={t().today.previousDay}
      >
        <ChevronLeft className="size-4" aria-hidden />
      </Link>
      <form action="/" className="flex items-center gap-1.5">
        {state.status !== "all" ? (
          <input type="hidden" name="status" value={state.status} />
        ) : null}
        <label className="relative">
          <span className="sr-only">{t().today.pickDate}</span>
          <CalendarDays
            className="text-muted-foreground pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2"
            aria-hidden
          />
          <input
            type="date"
            name="date"
            defaultValue={day}
            className="bg-card num h-10 rounded-md border pr-2 pl-8 text-sm [color-scheme:inherit]"
          />
        </label>
        <button
          type="submit"
          className="bg-muted hover:bg-primary hover:text-primary-foreground h-10 rounded-md px-3 text-sm font-semibold transition-colors duration-150"
        >
          {t().today.show}
        </button>
      </form>
      <Link
        href={todayHref(state, { date: shiftDay(day, 1) })}
        className={ICON_BUTTON}
        aria-label={t().today.nextDay}
      >
        <ChevronRight className="size-4" aria-hidden />
      </Link>
      {!isToday ? (
        <Link
          href={todayHref(state, { date: undefined })}
          className="text-primary ml-1 text-sm font-semibold hover:underline"
        >
          {t().today.today}
        </Link>
      ) : null}
    </div>
  );
}

/** Tümü / Canlı / Yaklaşan / Biten as a segmented control of links with counts. */
export function StatusTabs({
  state,
  counts,
}: {
  state: TodayState;
  counts: Record<StatusFilter, number>;
}) {
  return (
    <nav aria-label={t().today.statusFilter} className="scroll-strip overflow-x-auto">
      <ul className="bg-card inline-flex gap-1 rounded-lg border p-1">
        {STATUS_FILTERS.map((status) => {
          const active = state.status === status;
          return (
            <li key={status}>
              <Link
                href={todayHref(state, { status })}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "inline-flex h-8 items-center gap-1.5 rounded-md px-3 text-sm font-medium whitespace-nowrap transition-colors duration-150",
                  active
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                {status === "live" ? (
                  <span
                    aria-hidden
                    className={cn(
                      "size-1.5 rounded-full",
                      counts.live > 0 ? "live-dot bg-live" : "bg-current opacity-50",
                    )}
                  />
                ) : null}
                {t().today[status]}
                <span
                  className={cn(
                    "num rounded px-1 text-xs",
                    active ? "bg-primary-foreground/15" : "bg-muted",
                  )}
                >
                  {counts[status]}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
