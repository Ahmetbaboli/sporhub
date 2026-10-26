import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { EventCard } from "@/components/sport/event-list";
import { EventCardsSkeleton } from "@/components/sport/skeletons";
import { TeamBadge } from "@/components/sport/team-badge";
import { EmptyState } from "@/components/ui/states";
import { api } from "@/lib/api";
import { orNotFound, parseId } from "@/lib/api-helpers";
import { groupSquad, splitTeamEvents } from "@/lib/events";
import { tr } from "@/lib/i18n/tr";
import type { TeamDetail } from "@/lib/types";

export const dynamic = "force-dynamic";

const EVENTS_FETCH_SIZE = 100;

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const team = await api.team(parseId(id)).catch(() => null);
  return { title: team?.name ?? tr.app.name };
}

export default async function TeamPage({ params }: Props) {
  const id = parseId((await params).id);
  // Existence is checked before anything streams so a missing team is a real HTTP 404.
  const team = await orNotFound(api.team(id));

  return (
    <>
      <div className="flex items-center gap-4">
        <TeamBadge team={team} size="lg" />
        <div>
          <h1 className="font-display text-4xl leading-none font-bold tracking-tight uppercase">
            {team.name}
          </h1>
          {team.country ? (
            <p className="text-muted-foreground mt-1 text-sm">{team.country}</p>
          ) : null}
        </div>
      </div>

      <Suspense fallback={<EventCardsSkeleton />}>
        <TeamEvents teamId={id} />
      </Suspense>
      <Squad team={team} />
    </>
  );
}

async function TeamEvents({ teamId }: { teamId: number }) {
  const events = await api.teamEvents(teamId, {
    order: "desc",
    pageSize: EVENTS_FETCH_SIZE,
  });
  const { recent, upcoming } = splitTeamEvents(events.items);
  return (
    <div className="mt-8 grid gap-6 lg:grid-cols-2">
      <div>
        {recent.length ? (
          <EventCard title={tr.team.recent} events={recent} showRound heading="h2" />
        ) : (
          <EmptyState title={tr.team.noRecent} />
        )}
      </div>
      <div>
        {upcoming.length ? (
          <EventCard title={tr.team.upcoming} events={upcoming} showRound heading="h2" />
        ) : (
          <EmptyState title={tr.team.noUpcoming} />
        )}
      </div>
    </div>
  );
}

function Squad({ team }: { team: TeamDetail }) {
  const squad = groupSquad(team.squad);
  return (
    <section aria-labelledby="squad" className="mt-8">
      <h2
        id="squad"
        className="font-display text-primary mb-3 text-2xl font-semibold uppercase"
      >
        {tr.team.squad}
      </h2>
      {squad.length === 0 ? (
        <EmptyState title={tr.team.noSquad} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {squad.map(({ group, players }) => (
            <div key={group} className="bg-card rounded-lg border">
              <h3 className="bg-muted/60 border-b px-3 py-2 text-sm font-semibold">
                {tr.team.positions[group]}
              </h3>
              <ul className="divide-y">
                {players.map((p) => (
                  <li key={p.id}>
                    <Link
                      href={`/players/${p.id}`}
                      className="hover:bg-muted/50 flex items-center justify-between gap-2 px-3 py-2 text-sm"
                    >
                      <span className="font-medium">{p.name}</span>
                      <span className="text-muted-foreground text-xs">
                        {p.nationality}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
