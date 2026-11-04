import Link from "next/link";
import { LocalTime } from "@/components/sport/local-time";
import { ScoreFlash } from "@/components/sport/score-flash";
import { TeamBadge } from "@/components/sport/team-badge";
import { TribuneStar } from "@/components/tribune/tribune-provider";
import { sideOf } from "@/lib/events";
import { t } from "@/lib/i18n";
import { scoreMayBeDelayed } from "@/lib/sources";
import type { Participant, SportEvent } from "@/lib/types";
import { badgeCode, cn } from "@/lib/utils";

/** Badge + full name on wider screens; on phones only the provider's short code (GAL). */
function TeamCell({
  participant,
  align,
  winner,
}: {
  participant?: Participant;
  align: "left" | "right";
  winner: boolean;
}) {
  const team = participant?.team;
  if (!team) return <span className="text-muted-foreground">—</span>;
  return (
    <Link
      href={`/teams/${team.id}`}
      className={cn(
        "group/team flex min-w-0 items-center gap-2.5",
        align === "right" && "flex-row-reverse text-right",
      )}
    >
      <span className="hidden sm:inline-flex">
        <TeamBadge team={team} size="sm" />
      </span>
      <span
        aria-hidden
        className={cn(
          "truncate text-sm group-hover/team:underline",
          winner ? "font-semibold" : "font-medium",
        )}
      >
        <span className="hidden sm:inline">{team.name}</span>
        <span className="sm:hidden">{badgeCode(team)}</span>
      </span>
      <span className="sr-only">{team.name}</span>
    </Link>
  );
}

function StatusCell({ event, showRound }: { event: SportEvent; showRound: boolean }) {
  const label =
    event.status === "live" ? (
      <span className="text-live inline-flex items-center gap-1 text-xs font-bold uppercase">
        <span aria-hidden className="live-dot size-1.5 rounded-full bg-current" />
        {t().event.live}
      </span>
    ) : event.status === "scheduled" ? (
      <LocalTime iso={event.start_time} className="num text-sm font-semibold" />
    ) : (
      <span
        className={cn(
          "text-xs font-semibold uppercase",
          event.status === "finished" ? "text-muted-foreground" : "text-accent",
        )}
      >
        {t().event[event.status]}
      </span>
    );
  return (
    <div className="flex flex-col items-start leading-tight">
      {label}
      {showRound && event.round ? (
        <span className="text-muted-foreground mt-0.5 text-[11px]">
          {t().competition.round} {event.round}
        </span>
      ) : null}
    </div>
  );
}

function Score({
  event,
  home,
  away,
}: {
  event: SportEvent;
  home?: Participant;
  away?: Participant;
}) {
  const hasScore = event.status === "finished" || event.status === "live";
  if (!hasScore || home?.score == null || away?.score == null) {
    return (
      <span aria-hidden className="text-muted-foreground text-center text-xs font-medium">
        –
      </span>
    );
  }
  return (
    <ScoreFlash
      value={`${home.score}-${away.score}`}
      label={`${home.score} - ${away.score}`}
      className={cn(
        "num bg-muted mx-auto inline-flex min-w-[3.75rem] justify-center gap-1 rounded-md px-1.5 py-1 text-sm font-bold whitespace-nowrap sm:gap-1.5 sm:px-2 sm:text-base",
        event.status === "live" && "text-live",
      )}
    >
      <span>{home.score}</span>
      <span aria-hidden className="text-muted-foreground font-normal">
        –
      </span>
      <span>{away.score}</span>
    </ScoreFlash>
  );
}

function matchName(home?: Participant, away?: Participant): string {
  return `${home?.team?.name ?? "—"} – ${away?.team?.name ?? "—"}`;
}

/** One fixture/result line: status|time · home · score · away · follow star. */
export function EventRow({
  event,
  showRound = false,
}: {
  event: SportEvent;
  showRound?: boolean;
}) {
  const home = sideOf(event, "home");
  const away = sideOf(event, "away");
  const finished =
    event.status === "finished" && home?.score != null && away?.score != null;
  const homeWon = finished && home!.score! > away!.score!;
  const awayWon = finished && away!.score! > home!.score!;
  return (
    <li
      className={cn(
        "hover:bg-muted/50 px-3 py-2 transition-colors duration-150",
        event.status === "live" && "border-l-live border-l-2",
      )}
    >
      <div className="grid grid-cols-[2.75rem_minmax(0,1fr)_5.25rem_minmax(0,1fr)_2.25rem] items-center gap-1.5 sm:grid-cols-[4rem_minmax(0,1fr)_5.5rem_minmax(0,1fr)_2.25rem] sm:gap-3">
        <StatusCell event={event} showRound={showRound} />
        <TeamCell participant={home} align="right" winner={homeWon} />
        {event.kind === "match" ? (
          <Link
            href={`/matches/${event.id}`}
            aria-label={`${t().match.open}: ${matchName(home, away)}`}
            className="hover:ring-primary/40 rounded-md text-center transition-shadow duration-150 hover:ring-2"
          >
            <Score event={event} home={home} away={away} />
          </Link>
        ) : (
          <div className="text-center">
            <Score event={event} home={home} away={away} />
          </div>
        )}
        <TeamCell participant={away} align="left" winner={awayWon} />
        <TribuneStar kind="matches" id={event.id} name={matchName(home, away)} />
      </div>
      {event.status === "live" && scoreMayBeDelayed(event.competition.source) ? (
        <p className="text-muted-foreground mt-1 text-center text-[11px] italic">
          {t().freshness.scoresDelayed}
        </p>
      ) : null}
    </li>
  );
}
