import Link from "next/link";
import { LocalTime } from "@/components/sport/local-time";
import { StatusBadge } from "@/components/sport/status-badge";
import { TeamBadge } from "@/components/sport/team-badge";
import { sideOf } from "@/lib/events";
import { tr } from "@/lib/i18n/tr";
import type { Participant, SportEvent } from "@/lib/types";
import { cn } from "@/lib/utils";

function TeamCell({
  participant,
  align,
}: {
  participant?: Participant;
  align: "left" | "right";
}) {
  const team = participant?.team;
  if (!team) return <span className="text-muted-foreground">—</span>;
  return (
    <Link
      href={`/teams/${team.id}`}
      className={cn(
        "flex min-w-0 items-center gap-2 hover:underline",
        align === "right" && "flex-row-reverse text-right",
      )}
    >
      <TeamBadge team={team} size="sm" />
      <span aria-hidden className="truncate text-sm font-medium">
        {team.short_name ?? team.name}
      </span>
      <span className="sr-only">{team.name}</span>
    </Link>
  );
}

function Centre({
  event,
  home,
  away,
}: {
  event: SportEvent;
  home?: Participant;
  away?: Participant;
}) {
  const hasScore = event.status === "finished" || event.status === "live";
  if (hasScore && home?.score != null && away?.score != null) {
    return (
      <span
        className={cn(
          "font-display num min-w-16 text-center text-xl font-bold",
          event.status === "live" && "text-accent",
        )}
        aria-label={`${home.score} - ${away.score}`}
      >
        {home.score} – {away.score}
      </span>
    );
  }
  return (
    <LocalTime
      iso={event.start_time}
      className="font-display num text-muted-foreground min-w-16 text-center text-lg font-semibold"
    />
  );
}

/** One fixture/result line: home — score|time — away, plus status. */
export function EventRow({
  event,
  showRound = false,
}: {
  event: SportEvent;
  showRound?: boolean;
}) {
  const home = sideOf(event, "home");
  const away = sideOf(event, "away");
  return (
    <li className="px-3 py-2.5">
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
        <TeamCell participant={home} align="right" />
        <Centre event={event} home={home} away={away} />
        <TeamCell participant={away} align="left" />
      </div>
      <div className="text-muted-foreground mt-1 flex items-center justify-center gap-2 text-xs">
        {event.status !== "scheduled" ? <StatusBadge status={event.status} /> : null}
        {showRound && event.round ? (
          <span>
            {tr.competition.round} {event.round}
          </span>
        ) : null}
      </div>
    </li>
  );
}
