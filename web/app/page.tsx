import Link from "next/link";
import { Suspense } from "react";
import { competitionHref, EventCard } from "@/components/sport/event-list";
import { EventCardsSkeleton } from "@/components/sport/skeletons";
import { EmptyState } from "@/components/ui/states";
import { api } from "@/lib/api";
import { groupBySportAndCompetition, sportLabel } from "@/lib/events";
import { tr } from "@/lib/i18n/tr";

// Data changes through the day; the API client caches each request for 60 s.
export const dynamic = "force-dynamic";

async function TodayEvents() {
  const today = await api.todayEvents();
  const groups = groupBySportAndCompetition(today.items);

  if (groups.length === 0) {
    return (
      <EmptyState title={tr.home.emptyTitle} body={tr.home.emptyBody}>
        <Link
          href="/football"
          className="text-primary mt-2 text-sm font-medium underline"
        >
          {tr.sports.football}
        </Link>
      </EmptyState>
    );
  }
  return (
    <div className="space-y-8">
      {groups.map((sport) => (
        <section key={sport.sportSlug} aria-labelledby={`sport-${sport.sportSlug}`}>
          <h2
            id={`sport-${sport.sportSlug}`}
            className="font-display text-primary mb-3 text-2xl font-semibold uppercase"
          >
            {sportLabel(sport.sportSlug)}
          </h2>
          <div className="space-y-4">
            {sport.competitions.map(({ competition, events }) => (
              <EventCard
                key={competition.id}
                title={competition.name}
                subtitle={competition.country ?? undefined}
                href={competitionHref(competition)}
                events={events}
                showRound
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

export default function HomePage() {
  return (
    <>
      <h1 className="font-display text-4xl font-bold tracking-tight uppercase">
        {tr.home.title}
      </h1>
      <p className="text-muted-foreground mt-1 mb-6 text-sm">{tr.home.subtitle}</p>
      <Suspense fallback={<EventCardsSkeleton cards={3} />}>
        <TodayEvents />
      </Suspense>
    </>
  );
}
