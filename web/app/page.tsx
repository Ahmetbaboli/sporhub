import Link from "next/link";
import { Suspense } from "react";
import { Freshness } from "@/components/layout/freshness";
import { TeamActivityCard } from "@/components/account/dashboard";
import { BreakingStrip, NewsBox } from "@/components/news/news-parts";
import { competitionHref, EventCard } from "@/components/sport/event-list";
import { EventCardsSkeleton } from "@/components/sport/skeletons";
import { EmptyState } from "@/components/ui/states";
import { api } from "@/lib/api";
import { groupBySportAndCompetition, sportLabel } from "@/lib/events";
import { initLocale, t } from "@/lib/i18n";
import { getViewer } from "@/lib/session";

// Data changes through the day; the API client caches each request for 60 s.
export const dynamic = "force-dynamic";

async function TodayEvents() {
  const today = await api.todayEvents();
  const groups = groupBySportAndCompetition(today.items);

  if (groups.length === 0) {
    return (
      <EmptyState title={t().home.emptyTitle} body={t().home.emptyBody}>
        <Link
          href="/football"
          className="text-primary mt-2 text-sm font-medium underline"
        >
          {t().sports.football}
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

const HOME_TEAM_CARDS = 2;
const BREAKING_LIMIT = 3;
const BREAKING_MAX_AGE_HOURS = 6;
const LATEST_NEWS = 6;

/** Breaking headlines from the last two days, above everything else. */
async function Breaking() {
  const page = await api
    .news({
      breaking: true,
      maxAgeHours: BREAKING_MAX_AGE_HOURS,
      pageSize: BREAKING_LIMIT,
    })
    .catch(() => null);
  return <BreakingStrip items={page?.items ?? []} />;
}

async function LatestNews() {
  const page = await api.news({ pageSize: LATEST_NEWS }).catch(() => null);
  return <NewsBox title={t().news.latest} items={page?.items ?? []} moreHref="/news" />;
}

/** Signed-in users see their own teams first; renders nothing for everyone else. */
async function PersonalAgenda() {
  const viewer = await getViewer().catch(() => null);
  if (!viewer) return null;
  const dashboard = await api.me.dashboard(await viewer.token()).catch(() => null);
  if (!dashboard?.teams.length) return null;
  return (
    <section aria-labelledby="my-agenda" className="mb-8">
      <div className="mb-3 flex items-baseline justify-between gap-2">
        <h2
          id="my-agenda"
          className="font-display text-primary text-2xl font-semibold uppercase"
        >
          {t().me.homeSection}
        </h2>
        <Link href="/me" className="text-primary text-sm font-medium hover:underline">
          {t().me.seeAll}
        </Link>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {dashboard.teams.slice(0, HOME_TEAM_CARDS).map((activity) => (
          <TeamActivityCard key={activity.team.id} activity={activity} />
        ))}
      </div>
    </section>
  );
}

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ account?: string }>;
}) {
  await initLocale();
  const { account } = await searchParams;
  return (
    <>
      {account === "deleted" ? (
        <p role="status" className="bg-card mb-6 rounded-lg border px-4 py-3 text-sm">
          {t().account.deleted}
        </p>
      ) : null}
      <Suspense fallback={null}>
        <Breaking />
      </Suspense>
      <Suspense fallback={null}>
        <PersonalAgenda />
      </Suspense>
      <h1 className="font-display text-4xl font-bold tracking-tight uppercase">
        {t().home.title}
      </h1>
      <p className="text-muted-foreground mt-1 mb-6 text-sm">{t().home.subtitle}</p>
      <Suspense fallback={<EventCardsSkeleton cards={3} />}>
        <TodayEvents />
      </Suspense>
      <Suspense fallback={null}>
        <LatestNews />
      </Suspense>
      <Suspense fallback={null}>
        <Freshness />
      </Suspense>
    </>
  );
}
