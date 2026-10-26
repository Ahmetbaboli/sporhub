import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { competitionHref, EventCard } from "@/components/sport/event-list";
import { TeamBadge } from "@/components/sport/team-badge";
import { EmptyState } from "@/components/ui/states";
import { api } from "@/lib/api";
import { orNotFound } from "@/lib/api-helpers";
import { sportLabel } from "@/lib/events";
import { tr } from "@/lib/i18n/tr";

export const dynamic = "force-dynamic";

const UPCOMING_PER_COMPETITION = 4;

type Props = { params: Promise<{ sport: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { sport } = await params;
  return { title: sportLabel(sport) };
}

export default async function SportPage({ params }: Props) {
  const { sport } = await params;
  const sports = await api.sports();
  const current = sports.items.find((s) => s.slug === sport);
  if (!current) notFound();

  const competitions = (await orNotFound(api.competitions(sport))).items;
  const upcoming = await Promise.all(
    competitions.map(async (competition) => ({
      competition,
      events: (
        await api.competitionEvents(competition.slug, {
          status: ["live", "scheduled"],
          pageSize: UPCOMING_PER_COMPETITION,
        })
      ).items,
    })),
  );

  return (
    <>
      <h1 className="font-display text-4xl font-bold tracking-tight uppercase">
        {current.name}
      </h1>

      {competitions.length === 0 ? (
        <EmptyState
          className="mt-6"
          title={tr.sports.comingSoon}
          body={tr.sports.comingSoonBody}
        />
      ) : (
        <>
          <h2 className="font-display text-primary mt-6 mb-3 text-2xl font-semibold uppercase">
            {tr.sport.competitions}
          </h2>
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {competitions.map((c) => (
              <li key={c.id}>
                <Link
                  href={competitionHref(c)}
                  className="bg-card hover:border-primary flex h-full items-center gap-3 rounded-lg border p-4"
                >
                  <TeamBadge team={{ name: c.name, logo_url: c.logo_url }} size="lg" />
                  <span>
                    <span className="font-display block text-xl leading-tight font-semibold">
                      {c.name}
                    </span>
                    <span className="text-muted-foreground text-sm">{c.country}</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>

          <h2 className="font-display text-primary mt-8 mb-3 text-2xl font-semibold uppercase">
            {tr.sport.upcoming}
          </h2>
          <div className="space-y-4">
            {upcoming.every((u) => u.events.length === 0) ? (
              <EmptyState title={tr.sport.noUpcoming} />
            ) : (
              upcoming
                .filter((u) => u.events.length > 0)
                .map(({ competition, events }) => (
                  <EventCard
                    key={competition.id}
                    title={competition.name}
                    href={competitionHref(competition)}
                    events={events}
                    showRound
                  />
                ))
            )}
          </div>
        </>
      )}
    </>
  );
}
