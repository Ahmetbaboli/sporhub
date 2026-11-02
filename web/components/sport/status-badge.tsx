import { t } from "@/lib/i18n";
import type { EventStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

export function StatusBadge({ status }: { status: EventStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded px-1.5 py-0.5 text-[11px] font-semibold tracking-wide uppercase",
        status === "live" && "bg-accent text-accent-foreground",
        status === "finished" && "bg-muted text-muted-foreground",
        (status === "postponed" || status === "cancelled") &&
          "border-accent text-accent border",
        status === "scheduled" && "text-muted-foreground",
      )}
    >
      {status === "live" ? (
        <span aria-hidden className="live-dot size-1.5 rounded-full bg-current" />
      ) : null}
      {t().event[status]}
    </span>
  );
}
