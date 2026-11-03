import Link from "next/link";
import { competitionHref } from "@/components/sport/event-list";
import { LocalTime } from "@/components/sport/local-time";
import { ScoreFlash } from "@/components/sport/score-flash";
import { TeamBadge } from "@/components/sport/team-badge";
import { TribuneStar } from "@/components/tribune/tribune-provider";
import { sideOf } from "@/lib/events";
import { t } from "@/lib/i18n";
import type { Participant, SportEvent } from "@/lib/types";
import { cn } from "@/lib/utils";

function Side({ p }: { p?: Participant }) {
  if (!p?.team) return <div />;
  return (
    <Link
      href={`/teams/${p.team.id}`}
      className="group/side flex min-w-0 flex-col items-center gap-2 text-center"
    >
      <TeamBadge team={p.team} size="lg" />
      <span className="line-clamp-2 text-sm leading-tight font-semibold group-hover/side:underline">
        {p.team.name}
      </span>
    </Link>
  );
}

/** Big card for one of the day's featured games. */
export function FeaturedMatch({ event }: { event: SportEvent }) {
  const home = sideOf(event, "home");
  const away = sideOf(event, "away");
  const live = event.status === "live";
  const scored =
    (live || event.status === "finished") && home?.score != null && away?.score != null;
  const name = `${home?.team?.name ?? "—"} – ${away?.team?.name ?? "—"}`;
  return (
    <article
      className={cn(
        "glass lift relative flex h-full flex-col gap-3 rounded-xl p-4",
        live && "border-live/60",
      )}
    >
      <header className="flex items-center justify-between gap-2 text-xs">
        <Link
          href={competitionHref(event.competition)}
          className="text-muted-foreground hover:text-foreground truncate font-medium"
        >
          {event.competition.name}
          {event.round ? ` · ${t().competition.round} ${event.round}` : ""}
        </Link>
        <TribuneStar kind="matches" id={event.id} name={name} className="-my-2 -mr-2" />
      </header>
      <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-3">
        <Side p={home} />
        <div className="flex flex-col items-center gap-1">
          {scored ? (
            <ScoreFlash
              value={`${home!.score}-${away!.score}`}
              label={`${home!.score} - ${away!.score}`}
              className={cn(
                "num px-1 text-3xl font-bold tracking-tight",
                live && "text-live",
              )}
            >
              {home!.score} – {away!.score}
            </ScoreFlash>
          ) : (
            <LocalTime iso={event.start_time} className="num text-2xl font-bold" />
          )}
          {live ? (
            <span className="text-live inline-flex items-center gap-1 text-xs font-bold uppercase">
              <span aria-hidden className="live-dot size-1.5 rounded-full bg-current" />
              {t().event.live}
            </span>
          ) : (
            <span className="text-muted-foreground text-xs font-semibold uppercase">
              {event.status === "scheduled"
                ? t().today.upcoming
                : t().event[event.status]}
            </span>
          )}
        </div>
        <Side p={away} />
      </div>
    </article>
  );
}
