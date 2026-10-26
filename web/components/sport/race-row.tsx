import Link from "next/link";
import { LocalTime } from "@/components/sport/local-time";
import { StatusBadge } from "@/components/sport/status-badge";
import { formatDay } from "@/lib/format";
import { tr } from "@/lib/i18n/tr";
import type { Participant, SportEvent } from "@/lib/types";
import { cn } from "@/lib/utils";

const PODIUM_SIZE = 3;

const text = (value: unknown): string | null =>
  typeof value === "string" && value ? value : null;

function DriverLink({ p }: { p: Participant }) {
  const name = text(p.extra.driver) ?? p.player?.name ?? "—";
  return p.player ? (
    <Link href={`/players/${p.player.id}`} className="font-medium hover:underline">
      {name}
    </Link>
  ) : (
    <span className="font-medium">{name}</span>
  );
}

function Podium({ participants }: { participants: Participant[] }) {
  return (
    <ol aria-label={tr.race.podium} className="mt-3 grid gap-1.5 sm:grid-cols-3">
      {participants.slice(0, PODIUM_SIZE).map((p) => (
        <li
          key={p.position}
          className={cn(
            "bg-muted/50 flex items-center gap-2 rounded-md px-2.5 py-1.5 text-sm",
            p.position === 1 && "border-primary border",
          )}
        >
          <span className="font-display num text-lg leading-none font-bold">
            {p.position}
          </span>
          <span className="min-w-0">
            <DriverLink p={p} />
            {p.team ? (
              <Link
                href={`/teams/${p.team.id}`}
                className="text-muted-foreground block truncate text-xs hover:underline"
              >
                {p.team.name}
              </Link>
            ) : null}
          </span>
        </li>
      ))}
    </ol>
  );
}

function FullResults({ participants }: { participants: Participant[] }) {
  return (
    <details className="mt-3 text-sm">
      <summary className="text-primary cursor-pointer font-medium">
        {tr.race.results}
      </summary>
      <div
        className="mt-2 overflow-x-auto"
        tabIndex={0}
        role="region"
        aria-label={tr.race.resultsTable}
      >
        <table className="num w-full min-w-[30rem] border-collapse text-xs">
          <caption className="sr-only">{tr.race.resultsTable}</caption>
          <thead className="text-muted-foreground uppercase">
            <tr>
              <th scope="col" className="px-2 py-1 text-center">
                {tr.race.position}
              </th>
              <th scope="col" className="px-2 py-1 text-left">
                {tr.race.driver}
              </th>
              <th scope="col" className="px-2 py-1 text-left">
                {tr.race.team}
              </th>
              <th scope="col" className="px-2 py-1 text-right">
                {tr.race.grid}
              </th>
              <th scope="col" className="px-2 py-1 text-left">
                {tr.race.result}
              </th>
              <th scope="col" className="px-2 py-1 text-right">
                {tr.race.points}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {participants.map((p) => (
              <tr key={p.position}>
                <td className="px-2 py-1 text-center font-semibold">{p.position}</td>
                <th scope="row" className="px-2 py-1 text-left font-normal">
                  <DriverLink p={p} />
                </th>
                <td className="px-2 py-1">{p.team?.name}</td>
                <td className="px-2 py-1 text-right">{String(p.extra.grid ?? "–")}</td>
                <td className="px-2 py-1">
                  {text(p.extra.time) ?? text(p.extra.status) ?? "–"}
                </td>
                <td className="px-2 py-1 text-right font-semibold">{p.points ?? 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}

/** Race card: grand prix, circuit, start time and (once finished) the podium + full result. */
export function RaceRow({ event }: { event: SportEvent }) {
  const finished = event.status === "finished" && event.participants.length > 0;
  const sessions = (event.extra.sessions ?? {}) as Record<string, string>;
  return (
    <li className="px-3 py-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-muted-foreground text-xs font-semibold uppercase">
            {event.round ? tr.race.round(event.round) : null}
          </p>
          <p className="font-display text-xl leading-tight font-semibold">{event.name}</p>
          {event.venue ? (
            <p className="text-muted-foreground text-sm">{event.venue}</p>
          ) : null}
        </div>
        <div className="text-right text-sm">
          <StatusBadge status={event.status} />
          <p className="text-muted-foreground mt-1 text-xs">
            {formatDay(event.start_time)}
          </p>
          <LocalTime
            iso={event.start_time}
            className="font-display num text-lg font-semibold"
          />
        </div>
      </div>
      {finished ? (
        <>
          <Podium participants={event.participants} />
          {event.participants.length > PODIUM_SIZE ? (
            <FullResults participants={event.participants} />
          ) : null}
        </>
      ) : sessions.qualifying ? (
        <p className="text-muted-foreground mt-2 text-xs">
          {tr.race.qualifying}: {formatDay(sessions.qualifying)}{" "}
          <LocalTime iso={sessions.qualifying} />
        </p>
      ) : null}
    </li>
  );
}
