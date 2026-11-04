import { ArrowDown, ArrowLeftRight, ArrowUp, CircleDot } from "lucide-react";
import Link from "next/link";
import { competitionHref } from "@/components/sport/event-list";
import { LocalDateTime } from "@/components/sport/local-date-time";
import { TeamBadge } from "@/components/sport/team-badge";
import { sideOf } from "@/lib/events";
import { formationLines, pitchName } from "@/lib/lineup";
import { t } from "@/lib/i18n";
import { providerName } from "@/lib/sources";
import type {
  Incident,
  Lineup,
  LineupPlayer,
  MatchDetails,
  MatchStat,
  Participant,
  SportEvent,
} from "@/lib/types";
import { cn } from "@/lib/utils";

const PERCENT_STATS = new Set(["possession", "pass_accuracy"]);

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="bg-card overflow-hidden rounded-xl border">
      <h2 className="border-b px-4 py-2.5 text-sm font-semibold">{title}</h2>
      <div className="p-4">{children}</div>
    </section>
  );
}

function HeaderTeam({ participant }: { participant?: Participant }) {
  const team = participant?.team;
  if (!team) return <span className="text-muted-foreground">—</span>;
  return (
    <Link
      href={`/teams/${team.id}`}
      className="group flex min-w-0 flex-col items-center gap-2 text-center"
    >
      <TeamBadge team={team} size="lg" />
      <span className="font-display line-clamp-2 text-base leading-tight font-semibold group-hover:underline sm:text-xl">
        {team.name}
      </span>
    </Link>
  );
}

function HeaderScore({ event }: { event: SportEvent }) {
  const home = sideOf(event, "home");
  const away = sideOf(event, "away");
  const hasScore =
    (event.status === "finished" || event.status === "live") &&
    home?.score != null &&
    away?.score != null;
  return (
    <div className="flex flex-col items-center gap-1.5">
      {hasScore ? (
        <span
          className={cn(
            "num font-display text-4xl font-bold sm:text-5xl",
            event.status === "live" && "text-live",
          )}
        >
          {home!.score} <span className="text-muted-foreground font-normal">–</span>{" "}
          {away!.score}
        </span>
      ) : (
        <LocalDateTime iso={event.start_time} className="num text-sm font-semibold" />
      )}
      <span
        className={cn(
          "text-xs font-semibold uppercase",
          event.status === "live" ? "text-live" : "text-muted-foreground",
        )}
      >
        {event.status === "live" && typeof event.extra.clock === "string"
          ? `${t().event.live} · ${event.extra.clock}`
          : t().event[event.status]}
      </span>
    </div>
  );
}

/** Competition · round · kick-off · venue, then home – score – away. */
export function MatchHeader({
  event,
  attendance,
}: {
  event: SportEvent;
  attendance?: number | null;
}) {
  const comp = event.competition;
  return (
    <header className="bg-card rounded-xl border p-4 sm:p-6">
      <p className="text-muted-foreground flex flex-wrap items-center justify-center gap-x-2 gap-y-1 text-xs">
        <Link href={competitionHref(comp)} className="hover:text-foreground font-medium">
          {comp.name}
        </Link>
        {event.round ? (
          <span>
            · {t().competition.round} {event.round}
          </span>
        ) : null}
        <span>
          · <LocalDateTime iso={event.start_time} />
        </span>
      </p>
      <div className="mt-5 grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-3 sm:gap-6">
        <HeaderTeam participant={sideOf(event, "home")} />
        <HeaderScore event={event} />
        <HeaderTeam participant={sideOf(event, "away")} />
      </div>
      {event.venue || attendance ? (
        <p className="text-muted-foreground mt-5 text-center text-xs">
          {event.venue ? `${t().event.venue}: ${event.venue}` : null}
          {event.venue && attendance ? " · " : null}
          {attendance
            ? `${t().match.attendance}: ${attendance.toLocaleString("tr-TR")}`
            : null}
        </p>
      ) : null}
    </header>
  );
}

function statText(stat: MatchStat, value: number | null): string {
  if (value == null) return "–";
  return PERCENT_STATS.has(stat.key) ? `%${Math.round(value)}` : String(value);
}

/** Home value · label · away value, with two bars sharing the row's total. */
export function MatchStats({ stats }: { stats: MatchStat[] }) {
  return (
    <Section title={t().match.stats}>
      <ul className="space-y-3.5">
        {stats.map((stat) => {
          const home = stat.home ?? 0;
          const away = stat.away ?? 0;
          const total = home + away;
          const homeShare = total ? (home / total) * 100 : 50;
          const lead = home === away ? null : home > away ? "home" : "away";
          return (
            <li key={stat.key}>
              <div className="num flex items-baseline justify-between text-sm">
                <span className={cn(lead === "home" && "font-bold")}>
                  {statText(stat, stat.home)}
                </span>
                <span className="text-muted-foreground text-xs">
                  {t().match.statLabels[stat.key] ?? stat.key}
                </span>
                <span className={cn(lead === "away" && "font-bold")}>
                  {statText(stat, stat.away)}
                </span>
              </div>
              <div
                aria-hidden
                className="bg-muted mt-1.5 flex h-1.5 gap-0.5 overflow-hidden rounded-full"
              >
                <div
                  className={cn(
                    "rounded-full",
                    lead === "home" ? "bg-primary" : "bg-primary/40",
                  )}
                  style={{ width: `${homeShare}%` }}
                />
                <div
                  className={cn(
                    "flex-1 rounded-full",
                    lead === "away" ? "bg-accent" : "bg-accent/40",
                  )}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </Section>
  );
}

function IncidentIcon({ kind }: { kind: Incident["kind"] }) {
  const label = t().match.incidents[kind];
  if (kind === "yellow_card" || kind === "red_card") {
    return (
      <span
        role="img"
        aria-label={label}
        className={cn(
          "inline-block h-3.5 w-2.5 rounded-[2px]",
          kind === "yellow_card" ? "bg-yellow-400" : "bg-red-600",
        )}
      />
    );
  }
  if (kind === "substitution") {
    return (
      <ArrowLeftRight
        role="img"
        aria-label={label}
        className="text-muted-foreground size-4"
      />
    );
  }
  return (
    <CircleDot
      role="img"
      aria-label={label}
      className={cn("size-4", kind === "own_goal" ? "text-red-500" : "text-primary")}
    />
  );
}

function IncidentText({ incident }: { incident: Incident }) {
  if (incident.kind === "substitution") {
    return (
      <span className="flex min-w-0 flex-col leading-tight">
        <span className="inline-flex items-center gap-1 truncate">
          <ArrowUp
            aria-label={t().match.subOn}
            className="size-3 shrink-0 text-emerald-500"
          />
          {incident.player}
        </span>
        {incident.related_player ? (
          <span className="text-muted-foreground inline-flex items-center gap-1 truncate text-xs">
            <ArrowDown
              aria-label={t().match.subOff}
              className="size-3 shrink-0 text-red-500"
            />
            {incident.related_player}
          </span>
        ) : null}
      </span>
    );
  }
  const goal = incident.kind !== "yellow_card" && incident.kind !== "red_card";
  return (
    <span className="flex min-w-0 flex-col leading-tight">
      <span className={cn("truncate", goal && "font-semibold")}>
        {incident.player ?? "—"}
      </span>
      {incident.kind === "own_goal" || incident.kind === "penalty_goal" ? (
        <span className="text-muted-foreground text-xs">
          {t().match.incidents[incident.kind]}
        </span>
      ) : null}
    </span>
  );
}

/** Goals, cards and substitutions in order; home on the left, away on the right. */
export function MatchTimeline({ incidents }: { incidents: Incident[] }) {
  return (
    <Section title={t().match.timeline}>
      {incidents.length ? (
        <ol className="space-y-2.5">
          {incidents.map((incident, i) => {
            const away = incident.side === "away";
            return (
              <li
                key={`${incident.minute}-${incident.kind}-${i}`}
                className="grid grid-cols-[minmax(0,1fr)_3.25rem_minmax(0,1fr)] items-center gap-2 text-sm"
              >
                <div className="flex min-w-0 items-center justify-end gap-2 text-right">
                  {away ? null : (
                    <>
                      <IncidentText incident={incident} />
                      <IncidentIcon kind={incident.kind} />
                    </>
                  )}
                </div>
                <span className="num bg-muted rounded-md py-0.5 text-center text-xs font-semibold">
                  {incident.minute}
                </span>
                <div className="flex min-w-0 items-center gap-2">
                  {away ? (
                    <>
                      <IncidentIcon kind={incident.kind} />
                      <IncidentText incident={incident} />
                    </>
                  ) : null}
                </div>
              </li>
            );
          })}
        </ol>
      ) : (
        <p className="text-muted-foreground text-sm">{t().match.noTimeline}</p>
      )}
    </Section>
  );
}

function PitchPlayer({ player, side }: { player: LineupPlayer; side: "home" | "away" }) {
  return (
    <li className="flex w-14 flex-col items-center gap-0.5 sm:w-20" title={player.name}>
      <span
        className={cn(
          "num relative inline-flex size-7 items-center justify-center rounded-full text-[11px] font-bold shadow sm:size-8",
          side === "home"
            ? "bg-primary text-primary-foreground"
            : "bg-accent text-accent-foreground",
        )}
      >
        {player.number ?? ""}
        {player.subbed_out ? (
          <ArrowDown
            aria-label={t().match.subOff}
            className="absolute -top-1 -right-1.5 size-3.5 rounded-full bg-white p-0.5 text-red-600"
          />
        ) : null}
      </span>
      <span className="w-full truncate text-center text-[10px] font-medium text-white drop-shadow sm:text-xs">
        {pitchName(player.name)}
      </span>
    </li>
  );
}

/** Both XIs on one pitch: home attacks upwards from the bottom, away downwards from the top. */
function Pitch({ home, away }: { home: Lineup; away: Lineup }) {
  const homeLines = formationLines(home);
  const awayLines = formationLines(away);
  if (!homeLines || !awayLines) return null;
  const row = (line: LineupPlayer[], side: "home" | "away", key: string) => (
    <ul key={key} className="flex justify-around">
      {line.map((p) => (
        <PitchPlayer key={`${p.external_id}-${p.name}`} player={p} side={side} />
      ))}
    </ul>
  );
  return (
    <div
      aria-hidden
      className="relative mb-5 overflow-hidden rounded-lg bg-emerald-700 px-1 py-3 dark:bg-emerald-900"
    >
      <div className="pointer-events-none absolute inset-2 rounded border border-white/30" />
      <div className="pointer-events-none absolute inset-x-2 top-1/2 border-t border-white/30" />
      <div className="pointer-events-none absolute top-1/2 left-1/2 size-16 -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/30" />
      <div className="relative flex flex-col gap-3">
        {/* Away from the top, keeper first, mirrored so their left is the viewer's right. */}
        {awayLines.map((line, i) => row([...line].reverse(), "away", `a${i}`))}
        <div className="h-2" />
        {[...homeLines].reverse().map((line, i) => row(line, "home", `h${i}`))}
      </div>
    </div>
  );
}

function PlayerLine({ player }: { player: LineupPlayer }) {
  return (
    <li className="flex items-center gap-2 py-1 text-sm">
      <span className="num text-muted-foreground w-6 shrink-0 text-right text-xs">
        {player.number}
      </span>
      <span className="min-w-0 flex-1 truncate">{player.name}</span>
      {player.subbed_in ? (
        <ArrowUp aria-label={t().match.subOn} className="size-3.5 text-emerald-500" />
      ) : null}
      {player.subbed_out ? (
        <ArrowDown aria-label={t().match.subOff} className="size-3.5 text-red-500" />
      ) : null}
      <span className="text-muted-foreground w-10 shrink-0 text-right text-[11px]">
        {player.position && player.position !== "SUB" ? player.position : ""}
      </span>
    </li>
  );
}

function TeamSheet({ lineup, name }: { lineup: Lineup; name: string }) {
  return (
    <div className="min-w-0">
      <h3 className="flex items-baseline justify-between gap-2 text-sm font-semibold">
        <span className="truncate">{name}</span>
        {lineup.formation ? (
          <span className="text-muted-foreground num shrink-0 text-xs font-normal">
            {t().match.formation}: {lineup.formation}
          </span>
        ) : null}
      </h3>
      <p className="text-muted-foreground mt-3 text-xs font-semibold uppercase">
        {t().match.starters}
      </p>
      <ul className="divide-y">
        {lineup.starters.map((p) => (
          <PlayerLine key={`${p.external_id}-${p.name}`} player={p} />
        ))}
      </ul>
      {lineup.substitutes.length ? (
        <>
          <p className="text-muted-foreground mt-4 text-xs font-semibold uppercase">
            {t().match.substitutes}
          </p>
          <ul className="divide-y">
            {lineup.substitutes.map((p) => (
              <PlayerLine key={`${p.external_id}-${p.name}`} player={p} />
            ))}
          </ul>
        </>
      ) : null}
    </div>
  );
}

export function MatchLineups({
  details,
  event,
}: {
  details: MatchDetails;
  event: SportEvent;
}) {
  const home = details.lineups.find((l) => l.side === "home");
  const away = details.lineups.find((l) => l.side === "away");
  if (!home && !away) return null;
  return (
    <Section title={t().match.lineups}>
      {home && away ? <Pitch home={home} away={away} /> : null}
      <div className="grid gap-6 sm:grid-cols-2">
        {home ? (
          <TeamSheet lineup={home} name={sideOf(event, "home")?.team?.name ?? ""} />
        ) : null}
        {away ? (
          <TeamSheet lineup={away} name={sideOf(event, "away")?.team?.name ?? ""} />
        ) : null}
      </div>
    </Section>
  );
}

export function MatchSourceNote({ source }: { source: string | null }) {
  if (!source) return null;
  return (
    <p className="text-muted-foreground text-center text-xs">
      {t().match.source}: {providerName(source)}
    </p>
  );
}
