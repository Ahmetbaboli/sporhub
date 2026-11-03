import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { Freshness } from "@/components/layout/freshness";
import { FavoriteToggle } from "@/components/account/favorite-toggle";
import { DayGroupedEvents } from "@/components/sport/event-list";
import { TableSkeleton } from "@/components/sport/skeletons";
import { ChampionshipTables } from "@/components/sport/championship-tables";
import { CompetitionStatsView } from "@/components/sport/competition-stats";
import { ConferenceStandings } from "@/components/sport/conference-standings";
import { StandingsTable } from "@/components/sport/standings-table";
import { EmptyState } from "@/components/ui/states";
import { Pagination } from "@/components/ui/pagination";
import { TabNav } from "@/components/ui/tab-nav";
import { TeamBadge } from "@/components/sport/team-badge";
import { TribuneStar } from "@/components/tribune/tribune-provider";
import { api } from "@/lib/api";
import { orNotFound, parsePage } from "@/lib/api-helpers";
import { initLocale, t } from "@/lib/i18n";
import { templateFor, type SportTemplate, type StandingsLayout } from "@/lib/sports";

export const dynamic = "force-dynamic";

const TABS = ["fixtures", "results", "standings", "stats"] as const;
type Tab = (typeof TABS)[number];

type Props = {
  params: Promise<{ sport: string; competition: string }>;
  searchParams: Promise<{ tab?: string; page?: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  await initLocale();
  const { competition } = await params;
  const detail = await api.competition(competition).catch(() => null);
  return { title: detail?.name ?? t().app.name };
}

function parseTab(value: string | undefined): Tab {
  return TABS.includes(value as Tab) ? (value as Tab) : "standings";
}

export default async function CompetitionPage({ params, searchParams }: Props) {
  await initLocale();
  const { sport, competition: ref } = await params;
  const query = await searchParams;
  const tab = parseTab(query.tab);
  const page = parsePage(query.page);

  const competition = await orNotFound(api.competition(ref));
  if (competition.sport_slug !== sport) notFound();

  const template = templateFor(sport);
  const base = `/${sport}/${competition.slug}`;
  const tabs = TABS.map((id) => ({
    id,
    label: template.tabs(t())[id],
    href: `${base}?tab=${id}`,
  }));

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-4">
          <TeamBadge team={competition} size="lg" variant="competition" />
          <div className="min-w-0">
            <h1 className="font-display text-4xl leading-none font-bold tracking-tight sm:text-5xl">
              {competition.name}
            </h1>
            <p className="text-muted-foreground mt-1.5 text-sm">
              {[
                competition.country,
                competition.current_season
                  ? `${t().competition.season} ${competition.current_season.year_label}`
                  : null,
              ]
                .filter(Boolean)
                .join(" · ")}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <TribuneStar
            kind="competitions"
            id={competition.id}
            name={competition.name}
            withText
          />
          <Suspense fallback={null}>
            <FavoriteToggle
              kind="competitions"
              id={competition.id}
              name={competition.name}
              returnTo={base}
            />
          </Suspense>
        </div>
      </div>
      <div className="mb-5" />

      <TabNav tabs={tabs} active={tab} />

      <Suspense key={`${tab}-${page}`} fallback={<TableSkeleton />}>
        {tab === "standings" ? (
          <StandingsTab competition={competition.slug} layout={template.standings} />
        ) : tab === "stats" ? (
          <StatsTab competition={competition.slug} template={template} />
        ) : (
          <EventsTab
            competition={competition.slug}
            tab={tab}
            page={page}
            pageSize={template.pageSize}
            hrefFor={(p) => `${base}?tab=${tab}&page=${p}`}
          />
        )}
      </Suspense>
      <Suspense fallback={null}>
        <Freshness sport={sport} />
      </Suspense>
    </>
  );
}

async function StandingsTab({
  competition,
  layout,
}: {
  competition: string;
  layout: StandingsLayout;
}) {
  const standings = await api.standings(competition);
  if (standings.items.length === 0)
    return <EmptyState title={t().competition.noStandings} />;
  switch (layout) {
    case "championship":
      return <ChampionshipTables rows={standings.items} />;
    case "conference":
      return <ConferenceStandings rows={standings.items} />;
    default:
      return <StandingsTable rows={standings.items} />;
  }
}

async function StatsTab({
  competition,
  template,
}: {
  competition: string;
  template: SportTemplate;
}) {
  const stats = await api.competitionStats(competition);
  return <CompetitionStatsView stats={stats} template={template} />;
}

async function EventsTab({
  competition,
  tab,
  page,
  pageSize,
  hrefFor,
}: {
  competition: string;
  tab: "fixtures" | "results";
  page: number;
  pageSize: number;
  hrefFor: (page: number) => string;
}) {
  const isResults = tab === "results";
  const events = await api.competitionEvents(competition, {
    status: isResults ? ["finished"] : ["live", "scheduled", "postponed"],
    order: isResults ? "desc" : "asc",
    page,
    pageSize,
  });
  if (events.items.length === 0) {
    return (
      <EmptyState
        title={isResults ? t().competition.noResults : t().competition.noFixtures}
      />
    );
  }
  return (
    <>
      <DayGroupedEvents events={events.items} />
      <Pagination
        page={page}
        pageSize={pageSize}
        total={events.total}
        hrefFor={hrefFor}
      />
    </>
  );
}
