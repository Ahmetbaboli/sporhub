import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Freshness } from "@/components/layout/freshness";
import { FavoriteToggle } from "@/components/account/favorite-toggle";
import { EventCard } from "@/components/sport/event-list";
import { EventCardsSkeleton } from "@/components/sport/skeletons";
import { RelatedNews } from "@/components/news/related-news";
import { SeriesChart } from "@/components/charts/series-chart";
import { CompareLink } from "@/components/compare/compare-link";
import { HeadToHeadCard, TeamAnalysisPanel } from "@/components/sport/team-analysis";
import { TeamBadge } from "@/components/sport/team-badge";
import { TribuneStar } from "@/components/tribune/tribune-provider";
import { EmptyState } from "@/components/ui/states";
import { api } from "@/lib/api";
import { orNotFound, parseId } from "@/lib/api-helpers";
import { groupSquad, splitTeamEvents } from "@/lib/events";
import { initLocale, t } from "@/lib/i18n";
import { teamProgression } from "@/lib/series";
import { templateFor } from "@/lib/sports";
import type { TeamDetail } from "@/lib/types";

export const dynamic = "force-dynamic";

const EVENTS_FETCH_SIZE = 100;
const MIN_CHART_POINTS = 2;

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  await initLocale();
  const { id } = await params;
  const team = await api.team(parseId(id)).catch(() => null);
  return { title: team?.name ?? t().app.name };
}

export default async function TeamPage({ params }: Props) {
  await initLocale();
  const id = parseId((await params).id);
  // Existence is checked before anything streams so a missing team is a real HTTP 404.
  const team = await orNotFound(api.team(id));

  return (
    <>
      <div className="flex flex-wrap items-center gap-4">
        <TeamBadge team={team} size="lg" />
        <div>
          <h1 className="font-display text-4xl leading-none font-bold tracking-tight">
            {team.name}
          </h1>
          {team.country ? (
            <p className="text-muted-foreground mt-1 text-sm">{team.country}</p>
          ) : null}
        </div>
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <CompareLink href={`/compare?type=teams&a=${id}`} />
          <TribuneStar kind="teams" id={id} name={team.name} withText />
          <Suspense fallback={null}>
            <FavoriteToggle
              kind="teams"
              id={id}
              name={team.name}
              returnTo={`/teams/${id}`}
            />
          </Suspense>
        </div>
      </div>

      <Suspense fallback={<EventCardsSkeleton />}>
        <TeamEvents teamId={id} sport={team.sport_slug} />
      </Suspense>
      <Suspense fallback={null}>
        <TeamInsights teamId={id} sport={team.sport_slug} />
      </Suspense>
      <Suspense fallback={null}>
        <RelatedNews kind="team" id={id} name={team.name} />
      </Suspense>
      <Squad team={team} />
      <Suspense fallback={null}>
        <Freshness sport={team.sport_slug} />
      </Suspense>
    </>
  );
}

async function TeamEvents({ teamId, sport }: { teamId: number; sport: string | null }) {
  const isRace = sport === "formula-1";
  const events = await api.teamEvents(teamId, {
    order: "desc",
    pageSize: EVENTS_FETCH_SIZE,
  });
  const { recent, upcoming } = splitTeamEvents(events.items);
  return (
    <div className="mt-8 grid gap-6 lg:grid-cols-2">
      <div>
        {recent.length ? (
          <EventCard
            title={isRace ? t().team.recentRaces : t().team.recent}
            events={recent}
            showRound
            heading="h2"
          />
        ) : (
          <EmptyState title={t().team.noRecent} />
        )}
      </div>
      <div>
        {upcoming.length ? (
          <EventCard
            title={isRace ? t().team.upcomingRaces : t().team.upcoming}
            events={upcoming}
            showRound
            heading="h2"
          />
        ) : (
          <EmptyState title={t().team.noUpcoming} />
        )}
      </div>
    </div>
  );
}

/** Form, home/away split and head-to-head with the next opponent (match sports only). */
async function TeamInsights({ teamId, sport }: { teamId: number; sport: string | null }) {
  const rules = templateFor(sport ?? "").analysis;
  if (!rules) return null;
  const [analysis, events] = await Promise.all([
    api.teamAnalysis(teamId),
    api.teamEvents(teamId, { order: "desc", pageSize: EVENTS_FETCH_SIZE }),
  ]);
  const next = splitTeamEvents(events.items).upcoming[0];
  const opponent = next?.participants.find((p) => p.team && p.team.id !== teamId)?.team;
  const h2h = opponent
    ? await api.headToHead(teamId, opponent.id).catch(() => null)
    : null;
  const progression = teamProgression(events.items, teamId, rules.draws);
  return (
    <>
      <TeamAnalysisPanel analysis={analysis} rules={rules} />
      {progression.length >= MIN_CHART_POINTS ? (
        <div className="mt-4">
          <SeriesChart
            title={t().charts.progressionTitle}
            description={
              rules.draws ? t().charts.progressionPoints : t().charts.progressionWinPct
            }
            data={progression}
            valueLabel={rules.draws ? t().charts.points : t().charts.winPct}
            xLabel={t().charts.match}
            format={rules.draws ? "int" : "pct"}
          />
        </div>
      ) : null}
      {h2h && opponent ? (
        <HeadToHeadCard
          h2h={h2h}
          rules={rules}
          title={`${t().analysis.h2hTitle} · ${t().analysis.h2hNext(opponent.name)}`}
        />
      ) : null}
    </>
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
        {team.sport_slug === "formula-1" ? t().team.drivers : t().team.squad}
      </h2>
      {squad.length === 0 ? (
        <EmptyState title={t().team.noSquad} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {squad.map(({ group, players }) => (
            <div key={group} className="bg-card rounded-lg border">
              <h3 className="bg-muted/60 border-b px-3 py-2 text-sm font-semibold">
                {t().team.positions[group]}
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
