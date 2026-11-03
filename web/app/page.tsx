import Link from "next/link";
import { Suspense } from "react";
import { Freshness } from "@/components/layout/freshness";
import { TeamActivityCard } from "@/components/account/dashboard";
import { BreakingStrip, NewsRail } from "@/components/news/news-parts";
import { competitionHref, EventCard } from "@/components/sport/event-list";
import { LiveRefresher } from "@/components/sport/live-refresher";
import { EventCardsSkeleton } from "@/components/sport/skeletons";
import { FeaturedMatch } from "@/components/today/featured-match";
import { DatePicker, StatusTabs } from "@/components/today/today-controls";
import { EmptyState } from "@/components/ui/states";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { groupBySportAndCompetition, sportLabel } from "@/lib/events";
import { formatDay } from "@/lib/format";
import { initLocale, intlLocale, t } from "@/lib/i18n";
import { getViewer } from "@/lib/session";
import {
  countByStatus,
  matchesStatus,
  parseTodayState,
  pickFeatured,
  type TodayState,
  tribuneEvents,
} from "@/lib/today";
import { isTribuneEmpty, prioritize, type Tribune } from "@/lib/tribune";
import { getTribune } from "@/lib/tribune-server";
import type { SportEvent } from "@/lib/types";

// Data changes through the day; the API client caches each request for 60 s.
export const dynamic = "force-dynamic";

const HOME_TEAM_CARDS = 2;
const BREAKING_LIMIT = 3;
const BREAKING_MAX_AGE_HOURS = 6;
const LATEST_NEWS = 6;

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };

function teamIds(event: SportEvent): number[] {
  return event.participants.flatMap((p) => (p.team ? [p.team.id] : []));
}

function Featured({ events }: { events: SportEvent[] }) {
  if (events.length === 0) return null;
  return (
    <section aria-labelledby="featured" className="mb-6">
      <div className="mb-2 flex items-baseline justify-between gap-2">
        <h2 id="featured" className="text-lg font-bold">
          {t().today.featured}
        </h2>
        <span className="text-muted-foreground text-xs">{t().today.featuredHint}</span>
      </div>
      {/* Phones: one swipeable row; wider screens: a grid. */}
      <ul className="scroll-strip -mx-4 flex snap-x snap-mandatory gap-3 overflow-x-auto px-4 pb-1 sm:mx-0 sm:grid sm:grid-cols-2 sm:overflow-visible sm:[mask-image:none] sm:px-0 xl:grid-cols-3">
        {events.map((event) => (
          <li key={event.id} className="w-[85%] shrink-0 snap-start sm:w-auto">
            <FeaturedMatch event={event} />
          </li>
        ))}
      </ul>
    </section>
  );
}

function FromTribune({ events }: { events: SportEvent[] }) {
  if (events.length === 0) return null;
  return (
    <div className="mb-6">
      <EventCard
        title={t().tribune.forYouToday}
        subtitle={t().tribune.title}
        href="/tribun"
        events={events}
        heading="h2"
      />
    </div>
  );
}

async function DayEvents({ state, tribune }: { state: TodayState; tribune: Tribune }) {
  const day = await api.todayEvents({ date: state.date });
  const counts = countByStatus(day.items);
  const visible = day.items.filter((e) => matchesStatus(e, state.status));
  // Favourite leagues and teams first inside each sport.
  const ordered = prioritize(
    prioritize(visible, tribune.teams, teamIds),
    tribune.competitions,
    (e) => [e.competition.id],
  );
  const groups = groupBySportAndCompetition(ordered);
  const featured = state.status === "all" ? pickFeatured(day.items) : [];
  const mine = isTribuneEmpty(tribune) ? [] : tribuneEvents(visible, tribune);

  return (
    <>
      <LiveRefresher active={counts.live > 0} />
      <div className="mb-5">
        <StatusTabs state={state} counts={counts} />
      </div>
      {day.items.length === 0 ? (
        <EmptyState title={t().home.emptyTitle} body={t().home.emptyBody}>
          <Link
            href="/football"
            className="text-primary mt-2 text-sm font-medium underline"
          >
            {t().sports.football}
          </Link>
        </EmptyState>
      ) : visible.length === 0 ? (
        <EmptyState
          title={
            t().today.emptyStatus[state.status as Exclude<typeof state.status, "all">]
          }
        />
      ) : (
        <>
          <Featured events={featured} />
          <FromTribune events={mine} />
          <div className="space-y-7">
            {groups.map((sport) => (
              <section key={sport.sportSlug} aria-labelledby={`sport-${sport.sportSlug}`}>
                <h2
                  id={`sport-${sport.sportSlug}`}
                  className="text-muted-foreground mb-2 text-xs font-bold tracking-[0.12em] uppercase"
                >
                  {sportLabel(sport.sportSlug)}
                </h2>
                <div className="space-y-3">
                  {sport.competitions.map(({ competition, events }) => (
                    <EventCard
                      key={competition.id}
                      title={competition.name}
                      subtitle={competition.country ?? undefined}
                      href={competitionHref(competition)}
                      competition={competition}
                      events={events}
                      showRound
                    />
                  ))}
                </div>
              </section>
            ))}
          </div>
        </>
      )}
    </>
  );
}

function DaySkeleton() {
  return (
    <>
      <Skeleton className="mb-5 h-10 w-80 max-w-full" />
      <EventCardsSkeleton cards={3} />
    </>
  );
}

/** Breaking headlines from the last hours, above everything else. */
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
  return <NewsRail title={t().news.latest} items={page?.items ?? []} moreHref="/news" />;
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
        <h2 id="my-agenda" className="text-lg font-bold">
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

export default async function HomePage({ searchParams }: Props) {
  await initLocale();
  const params = await searchParams;
  const state = parseTodayState(params);
  const tribune = await getTribune();
  const title = state.date
    ? t().today.title(formatDay(`${state.date}T12:00:00Z`, "UTC", intlLocale()))
    : t().home.title;
  return (
    <>
      {params.account === "deleted" ? (
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
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_20rem] xl:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="min-w-0">
          <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h1 className="font-display text-4xl leading-none font-bold tracking-tight uppercase sm:text-5xl">
                {title}
              </h1>
              <p className="text-muted-foreground mt-1.5 text-sm">{t().home.subtitle}</p>
            </div>
            <DatePicker state={state} />
          </div>
          <Suspense key={`${state.date}-${state.status}`} fallback={<DaySkeleton />}>
            <DayEvents state={state} tribune={tribune} />
          </Suspense>
        </div>
        <aside className="min-w-0 lg:sticky lg:top-28 lg:self-start">
          <Suspense fallback={null}>
            <LatestNews />
          </Suspense>
        </aside>
      </div>
      <Suspense fallback={null}>
        <Freshness />
      </Suspense>
    </>
  );
}
