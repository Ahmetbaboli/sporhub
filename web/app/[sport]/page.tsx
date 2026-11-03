import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { SplitWords } from "@/components/motion/motion";
import {
  ChampionshipTop,
  NextRaceCard,
  RaceCalendar,
  UpcomingRaces,
} from "@/components/f1/f1-parts";
import { Freshness } from "@/components/layout/freshness";
import { competitionHref, EventCard } from "@/components/sport/event-list";
import { EventCardsSkeleton, TableSkeleton } from "@/components/sport/skeletons";
import { TeamBadge } from "@/components/sport/team-badge";
import { TribuneStar } from "@/components/tribune/tribune-provider";
import { EmptyState } from "@/components/ui/states";
import { api } from "@/lib/api";
import { orNotFound } from "@/lib/api-helpers";
import { sportLabel } from "@/lib/events";
import { nextRace, splitChampionship } from "@/lib/f1";
import { initLocale, t } from "@/lib/i18n";
import { prioritize } from "@/lib/tribune";
import { getTribune } from "@/lib/tribune-server";
import type { Competition } from "@/lib/types";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

const UPCOMING_PER_COMPETITION = 4;
const F1_SLUG = "formula-1";
const SEASON_RACES = 40;
const UPCOMING_RACES = 3;
const CHAMPIONSHIP_TOP = 10;

type Props = { params: Promise<{ sport: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  await initLocale();
  const { sport } = await params;
  return { title: sportLabel(sport) };
}

function SectionTitle({ id, children }: { id?: string; children: React.ReactNode }) {
  return (
    <h2 id={id} className="mb-3 text-lg font-bold">
      {children}
    </h2>
  );
}

export default async function SportPage({ params }: Props) {
  await initLocale();
  const { sport } = await params;
  // Existence is checked before anything streams so an unknown sport is a real HTTP 404.
  const sports = await api.sports();
  const current = sports.items.find((s) => s.slug === sport);
  if (!current) notFound();
  const [competitions, meta, tribune] = await Promise.all([
    orNotFound(api.competitions(sport)).then((page) => page.items),
    api.meta().catch(() => null),
    getTribune(),
  ]);
  const configured = meta?.sports.find((s) => s.slug === sport)?.configured ?? true;

  return (
    <>
      <h1 className="font-display text-4xl leading-none font-bold tracking-tight uppercase sm:text-5xl">
        <SplitWords text={current.name} />
      </h1>
      {competitions.length === 0 ? (
        <EmptyState
          className="mt-6"
          title={configured ? t().sports.awaitingSync : t().sports.notConfigured}
          body={configured ? t().sports.awaitingSyncBody : t().sports.notConfiguredBody}
        >
          <Link
            href="/sources"
            className="text-primary mt-2 text-sm font-medium underline"
          >
            {t().sports.sourcesLink}
          </Link>
        </EmptyState>
      ) : sport === F1_SLUG ? (
        <Suspense fallback={<TableSkeleton rows={8} />}>
          <FormulaOne competition={competitions[0]} />
        </Suspense>
      ) : (
        <Leagues
          competitions={prioritize(competitions, tribune.competitions, (c) => [c.id])}
          favorites={tribune.competitions}
        />
      )}
      <Suspense fallback={null}>
        <Freshness sport={sport} />
      </Suspense>
    </>
  );
}

/* ---- Football / basketball ------------------------------------------------------------ */

function LeagueCard({ c, starred }: { c: Competition; starred: boolean }) {
  return (
    <div
      className={cn(
        "bg-card lift relative flex h-full items-center gap-3 rounded-xl border p-3",
        starred && "border-accent/50",
      )}
    >
      <TeamBadge team={c} size="lg" variant="competition" />
      <Link
        href={competitionHref(c)}
        className="min-w-0 flex-1 after:absolute after:inset-0"
      >
        <span className="block truncate font-semibold">{c.name}</span>
        <span className="text-muted-foreground block truncate text-sm">{c.country}</span>
      </Link>
      <TribuneStar
        kind="competitions"
        id={c.id}
        name={c.name}
        className="relative z-10"
      />
    </div>
  );
}

function Leagues({
  competitions,
  favorites,
}: {
  competitions: Competition[];
  favorites: number[];
}) {
  const mine = competitions.filter((c) => favorites.includes(c.id));
  return (
    <>
      <p className="text-muted-foreground mt-1.5 mb-5 text-sm">
        {t().sport.leagueCount(competitions.length)}
      </p>
      {mine.length > 0 ? (
        <nav aria-label={t().sport.favoriteLeagues} className="mb-6">
          <p className="text-muted-foreground mb-2 text-xs font-bold tracking-[0.12em] uppercase">
            {t().sport.favoriteLeagues}
          </p>
          <ul className="scroll-strip flex gap-2 overflow-x-auto pb-1">
            {mine.map((c) => (
              <li key={c.id} className="shrink-0">
                <Link
                  href={competitionHref(c)}
                  className="bg-card hover:border-accent inline-flex h-11 items-center gap-2 rounded-full border pr-4 pl-1.5 text-sm font-semibold transition-colors duration-150"
                >
                  <TeamBadge team={c} size="sm" variant="competition" />
                  {c.name}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      ) : null}
      <section aria-labelledby="all-leagues">
        <SectionTitle id="all-leagues">{t().sport.allLeagues}</SectionTitle>
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {competitions.map((c) => (
            <li key={c.id}>
              <LeagueCard c={c} starred={favorites.includes(c.id)} />
            </li>
          ))}
        </ul>
      </section>
      <section aria-labelledby="upcoming" className="mt-8">
        <SectionTitle id="upcoming">{t().sport.upcoming}</SectionTitle>
        <Suspense fallback={<EventCardsSkeleton />}>
          <Upcoming competitions={competitions} />
        </Suspense>
      </section>
    </>
  );
}

async function Upcoming({ competitions }: { competitions: Competition[] }) {
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
  const nonEmpty = upcoming.filter((u) => u.events.length > 0);
  if (nonEmpty.length === 0) return <EmptyState title={t().sport.noUpcoming} />;
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      {nonEmpty.map(({ competition, events }) => (
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
  );
}

/* ---- Formula 1: its own layout, not the league template ----------------------------- */

async function FormulaOne({ competition }: { competition: Competition }) {
  const [season, standings, detail] = await Promise.all([
    api.competitionEvents(competition.slug, { order: "asc", pageSize: SEASON_RACES }),
    api.standings(competition.slug).catch(() => null),
    api.competition(competition.slug).catch(() => null),
  ]);
  const races = season.items.filter((e) => e.kind === "race");
  const next = nextRace(races);
  const after = next
    ? races
        .filter((r) => r.status === "scheduled" && r.start_time > next.start_time)
        .slice(0, UPCOMING_RACES)
    : [];
  const { drivers, constructors } = splitChampionship(standings?.items ?? []);
  const base = competitionHref(competition);

  return (
    <div className="mt-2 space-y-8">
      <p className="text-muted-foreground text-sm">
        {detail?.current_season ? t().f1.season(detail.current_season.year_label) : null}
      </p>
      {next ? <NextRaceCard race={next} /> : <EmptyState title={t().f1.noNextRace} />}

      {after.length > 0 ? (
        <section aria-labelledby="f1-upcoming">
          <SectionTitle id="f1-upcoming">{t().f1.upcoming}</SectionTitle>
          <UpcomingRaces races={after} />
        </section>
      ) : null}

      {drivers.length || constructors.length ? (
        <section aria-labelledby="f1-standings">
          <SectionTitle id="f1-standings">{t().f1.standings}</SectionTitle>
          <div className="grid gap-4 lg:grid-cols-2">
            <ChampionshipTop
              title={t().f1.driversTop}
              rows={drivers.slice(0, CHAMPIONSHIP_TOP)}
              kind="drivers"
              moreHref={`${base}?tab=standings`}
            />
            <ChampionshipTop
              title={t().f1.constructorsTop}
              rows={constructors.slice(0, CHAMPIONSHIP_TOP)}
              kind="constructors"
              moreHref={`${base}?tab=standings`}
            />
          </div>
        </section>
      ) : null}

      <section aria-labelledby="f1-calendar">
        <div className="mb-3 flex items-baseline justify-between gap-2">
          <h2 id="f1-calendar" className="text-lg font-bold">
            {t().f1.calendar}
          </h2>
          <Link
            href={`${base}?tab=results`}
            className="text-primary text-sm font-semibold hover:underline"
          >
            {t().competition.tabsBySport["formula-1"].results}
          </Link>
        </div>
        <RaceCalendar races={races} nextId={next?.id} />
      </section>
    </div>
  );
}
