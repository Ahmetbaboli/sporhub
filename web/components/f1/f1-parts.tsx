import { MapPin } from "lucide-react";
import Link from "next/link";
import { CircuitMap } from "@/components/f1/circuit-map";
import { Countdown } from "@/components/f1/countdown";
import { LocalDateTime } from "@/components/sport/local-date-time";
import { TribuneStar } from "@/components/tribune/tribune-provider";
import { circuitIdOf, circuitNameOf, placeOf, sessionsOf, winnerOf } from "@/lib/f1";
import { t } from "@/lib/i18n";
import type { SportEvent, Standing } from "@/lib/types";
import { cn } from "@/lib/utils";

const code = (value: unknown): string | null =>
  typeof value === "string" && value ? value : null;

/** The next grand prix: track map, place, start, live countdown and the weekend schedule. */
export function NextRaceCard({ race }: { race: SportEvent }) {
  const sessions = sessionsOf(race);
  const circuit = circuitNameOf(race);
  return (
    <article
      aria-labelledby="next-race"
      className="glass grid overflow-hidden rounded-2xl md:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]"
    >
      <div className="relative flex min-h-56 items-center justify-center bg-[radial-gradient(90%_80%_at_30%_20%,color-mix(in_srgb,var(--primary)_14%,transparent),transparent)] p-6 sm:min-h-72">
        <CircuitMap
          circuitId={circuitIdOf(race)}
          name={circuit}
          className="text-primary h-44 w-full max-w-md sm:h-60"
          strokeWidth={3}
        />
        <p className="text-muted-foreground absolute bottom-2 left-3 text-[10px]">
          {t().f1.trackCredit}
        </p>
      </div>
      <div className="space-y-4 border-t p-5 md:border-t-0 md:border-l">
        <div>
          <p className="text-accent text-xs font-bold tracking-[0.12em] uppercase">
            {t().f1.nextRace}
            {race.round ? ` · ${t().f1.round(race.round)}` : ""}
          </p>
          <h2
            id="next-race"
            className="font-display mt-1 text-3xl leading-none font-bold sm:text-4xl"
          >
            {race.name}
          </h2>
          <p className="text-muted-foreground mt-2 flex items-start gap-1.5 text-sm">
            <MapPin className="mt-0.5 size-4 shrink-0" aria-hidden />
            <span>
              {circuit}
              {placeOf(race) ? (
                <>
                  <br />
                  {placeOf(race)}
                </>
              ) : null}
            </span>
          </p>
        </div>
        <div>
          <p className="text-muted-foreground mb-1.5 text-xs font-semibold uppercase">
            {t().f1.countdown}
          </p>
          <Countdown iso={race.start_time} />
        </div>
        <div>
          <p className="text-muted-foreground mb-1.5 text-xs font-semibold uppercase">
            {t().f1.schedule}
          </p>
          <ol className="divide-y rounded-lg border">
            {sessions.map((s) => (
              <li
                key={s.key}
                className={cn(
                  "flex items-center justify-between gap-3 px-3 py-2 text-sm",
                  s.key === "race" && "bg-muted/60 font-semibold",
                )}
              >
                <span>{t().f1.sessions[s.key]}</span>
                <LocalDateTime iso={s.iso} className="num text-muted-foreground" />
              </li>
            ))}
          </ol>
          <p className="text-muted-foreground mt-1.5 text-[11px]">{t().f1.localTimes}</p>
        </div>
      </div>
    </article>
  );
}

/** Compact cards for the races after the next one. */
export function UpcomingRaces({ races }: { races: SportEvent[] }) {
  return (
    <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {races.map((race) => (
        <li
          key={race.id}
          className="bg-card lift flex items-center gap-3 rounded-xl border p-3"
        >
          <CircuitMap
            circuitId={circuitIdOf(race)}
            name={circuitNameOf(race)}
            className="text-foreground/70 size-16 shrink-0"
            strokeWidth={1.8}
          />
          <div className="min-w-0">
            <p className="text-muted-foreground text-[11px] font-semibold uppercase">
              {race.round ? t().f1.round(race.round) : null}
            </p>
            <p className="truncate font-semibold">{race.name}</p>
            <p className="text-muted-foreground truncate text-xs">{placeOf(race)}</p>
            <LocalDateTime iso={race.start_time} className="num text-xs font-medium" />
          </div>
        </li>
      ))}
    </ul>
  );
}

/** Top of the drivers' or constructors' championship, with tribune stars. */
export function ChampionshipTop({
  title,
  rows,
  kind,
  moreHref,
}: {
  title: string;
  rows: Standing[];
  kind: "drivers" | "constructors";
  moreHref: string;
}) {
  const leader = rows[0]?.points ?? 0;
  return (
    <section aria-label={title} className="bg-card overflow-hidden rounded-xl border">
      <header className="flex items-center justify-between border-b px-3 py-2">
        <h3 className="text-sm font-bold">{title}</h3>
        <Link
          href={moreHref}
          className="text-primary text-xs font-semibold hover:underline"
        >
          {t().f1.fullStandings}
        </Link>
      </header>
      <ol className="divide-y">
        {rows.map((row) => {
          const isDriver = kind === "drivers" && row.player;
          const name = isDriver ? row.player!.name : (row.team?.name ?? "—");
          const href = isDriver ? `/players/${row.player!.id}` : `/teams/${row.team?.id}`;
          const number = isDriver ? code(row.player!.extra.number) : null;
          const short = isDriver
            ? (code(row.extra.code) ?? code(row.player!.extra.code))
            : null;
          return (
            <li
              key={`${kind}-${row.position}-${name}`}
              className="flex items-center gap-2.5 px-3 py-1.5"
            >
              <span
                className={cn(
                  "num w-6 text-center text-sm font-bold",
                  row.position === 1 && "text-accent",
                )}
              >
                {row.position}
              </span>
              {isDriver ? (
                <span
                  aria-hidden
                  className="bg-muted num inline-flex h-7 w-9 shrink-0 items-center justify-center rounded-md border text-[11px] font-bold"
                >
                  {number ?? short ?? ""}
                </span>
              ) : null}
              <span className="min-w-0 flex-1">
                <Link
                  href={href}
                  className="block truncate text-sm font-medium hover:underline"
                >
                  {name}
                </Link>
                {isDriver && row.team ? (
                  <span className="text-muted-foreground block truncate text-xs">
                    {row.team.name}
                  </span>
                ) : null}
              </span>
              <span className="w-20 text-right">
                <span className="num text-sm font-bold">{row.points}</span>
                <span
                  aria-hidden
                  className="bg-muted mt-1 block h-1 overflow-hidden rounded-full"
                >
                  <span
                    className="bg-primary block h-full rounded-full"
                    style={{ width: `${leader ? (row.points / leader) * 100 : 0}%` }}
                  />
                </span>
              </span>
              {isDriver ? (
                <TribuneStar kind="players" id={row.player!.id} name={name} />
              ) : row.team ? (
                <TribuneStar kind="teams" id={row.team.id} name={name} />
              ) : null}
            </li>
          );
        })}
      </ol>
    </section>
  );
}

/** The whole season at a glance: round, grand prix, date and winner once finished. */
export function RaceCalendar({
  races,
  nextId,
}: {
  races: SportEvent[];
  nextId?: number;
}) {
  return (
    <ol className="bg-card divide-y overflow-hidden rounded-xl border">
      {races.map((race) => {
        const winner = winnerOf(race);
        const isNext = race.id === nextId;
        return (
          <li
            key={race.id}
            className={cn(
              "grid grid-cols-[2.5rem_3rem_minmax(0,1fr)_auto] items-center gap-3 px-3 py-2",
              isNext && "bg-primary/10",
            )}
          >
            <span className="num text-muted-foreground text-sm font-bold">
              {race.round}
            </span>
            <CircuitMap
              circuitId={circuitIdOf(race)}
              name={circuitNameOf(race)}
              className="text-foreground/60 h-8 w-12"
              strokeWidth={1.4}
            />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">{race.name}</p>
              <p className="text-muted-foreground truncate text-xs">{placeOf(race)}</p>
            </div>
            <div className="text-right text-xs">
              <LocalDateTime
                iso={race.start_time}
                withWeekday={false}
                className="num text-muted-foreground block"
              />
              {winner ? (
                <span className="font-medium">
                  {t().f1.winner}:{" "}
                  {(typeof winner.extra.driver === "string" && winner.extra.driver) ||
                    winner.player?.name}
                </span>
              ) : isNext ? (
                <span className="text-primary font-semibold">{t().f1.nextRace}</span>
              ) : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
