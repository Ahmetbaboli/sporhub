import Link from "next/link";
import { competitionHref } from "@/components/sport/event-list";
import { EventItem } from "@/components/sport/event-item";
import { TeamBadge } from "@/components/sport/team-badge";
import { tr } from "@/lib/i18n/tr";
import type {
  CompetitionPlace,
  Player,
  SportEvent,
  Standing,
  TeamActivity,
} from "@/lib/types";
import { cn } from "@/lib/utils";

export const SECTION_TITLE =
  "font-display text-primary mb-3 text-2xl font-semibold uppercase";

export function TeamActivityCard({ activity }: { activity: TeamActivity }) {
  const { team, recent, upcoming } = activity;
  return (
    <section className="bg-card overflow-hidden rounded-lg border">
      <header className="bg-muted/60 flex items-center gap-2 border-b px-3 py-2">
        <TeamBadge team={team} size="sm" />
        <h3 className="font-display text-lg font-semibold tracking-wide uppercase">
          <Link href={`/teams/${team.id}`} className="hover:underline">
            {team.name}
          </Link>
        </h3>
      </header>
      <EventGroup label={tr.me.recent} events={recent} />
      <EventGroup label={tr.me.upcoming} events={upcoming} />
    </section>
  );
}

function EventGroup({ label, events }: { label: string; events: SportEvent[] }) {
  if (events.length === 0) return null;
  return (
    <div>
      <p className="text-muted-foreground px-3 pt-2 text-xs font-semibold uppercase">
        {label}
      </p>
      <ul className="divide-y">
        {events.map((event) => (
          <EventItem key={event.id} event={event} />
        ))}
      </ul>
    </div>
  );
}

function rowName(row: Standing): { name: string; href: string | null } {
  if (row.player) return { name: row.player.name, href: `/players/${row.player.id}` };
  if (row.team) return { name: row.team.name, href: `/teams/${row.team.id}` };
  return { name: "—", href: null };
}

/** Top of a table plus the user's own rows (deduplicated, kept in table order). */
export function CompetitionPlaceCard({ place }: { place: CompetitionPlace }) {
  const mine = new Set(place.mine.map((r) => r.position));
  const shown = new Set(place.table.map((r) => r.position));
  const rows = [...place.table, ...place.mine.filter((r) => !shown.has(r.position))];
  return (
    <section className="bg-card overflow-hidden rounded-lg border">
      <header className="bg-muted/60 flex items-baseline justify-between gap-2 border-b px-3 py-2">
        <h3 className="font-display text-lg font-semibold tracking-wide uppercase">
          <Link href={competitionHref(place.competition)} className="hover:underline">
            {place.competition.name}
          </Link>
        </h3>
        {place.season ? (
          <span className="text-muted-foreground text-xs">{place.season.year_label}</span>
        ) : null}
      </header>
      <table className="num w-full text-sm">
        <caption className="sr-only">{place.competition.name}</caption>
        <tbody className="divide-y">
          {rows.map((row) => {
            const { name, href } = rowName(row);
            return (
              <tr
                key={`${row.position}-${name}`}
                className={cn(mine.has(row.position) && "bg-primary/10 font-semibold")}
              >
                <td className="w-10 px-3 py-1.5 text-right">{row.position}</td>
                <td className="px-2 py-1.5">
                  {href ? (
                    <Link href={href} className="hover:underline">
                      {name}
                    </Link>
                  ) : (
                    name
                  )}
                </td>
                <td className="w-14 px-3 py-1.5 text-right font-semibold">
                  {row.points}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

export function PlayerChips({ players }: { players: Player[] }) {
  return (
    <ul className="flex flex-wrap gap-2">
      {players.map((p) => (
        <li key={p.id}>
          <Link
            href={`/players/${p.id}`}
            className="bg-card hover:bg-muted inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm"
          >
            {p.team ? <TeamBadge team={p.team} size="sm" /> : null}
            <span className="font-medium">{p.name}</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
