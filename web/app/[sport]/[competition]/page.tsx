import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
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
import { api } from "@/lib/api";
import { orNotFound, parsePage } from "@/lib/api-helpers";
import { tr } from "@/lib/i18n/tr";
import { templateFor, type SportTemplate, type StandingsLayout } from "@/lib/sports";

export const dynamic = "force-dynamic";

const TABS = ["fixtures", "results", "standings", "stats"] as const;
type Tab = (typeof TABS)[number];

type Props = {
  params: Promise<{ sport: string; competition: string }>;
  searchParams: Promise<{ tab?: string; page?: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { competition } = await params;
  const detail = await api.competition(competition).catch(() => null);
  return { title: detail?.name ?? tr.app.name };
}

function parseTab(value: string | undefined): Tab {
  return TABS.includes(value as Tab) ? (value as Tab) : "standings";
}

export default async function CompetitionPage({ params, searchParams }: Props) {
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
    label: template.tabs[id],
    href: `${base}?tab=${id}`,
  }));

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-display text-4xl font-bold tracking-tight uppercase">
          {competition.name}
        </h1>
        <Suspense fallback={null}>
          <FavoriteToggle
            kind="competitions"
            id={competition.id}
            name={competition.name}
            returnTo={base}
          />
        </Suspense>
      </div>
      <p className="text-muted-foreground mt-1 mb-6 text-sm">
        {[
          competition.country,
          competition.current_season
            ? `${tr.competition.season} ${competition.current_season.year_label}`
            : null,
        ]
          .filter(Boolean)
          .join(" · ")}
      </p>

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
    return <EmptyState title={tr.competition.noStandings} />;
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
        title={isResults ? tr.competition.noResults : tr.competition.noFixtures}
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
