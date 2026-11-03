import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { SplitWords } from "@/components/motion/motion";
import { NewsFeed } from "@/components/news/news-parts";
import { competitionHref, EventCard } from "@/components/sport/event-list";
import { EventItem } from "@/components/sport/event-item";
import { EventCardsSkeleton } from "@/components/sport/skeletons";
import { TeamBadge } from "@/components/sport/team-badge";
import { ClearTribune } from "@/components/tribune/clear-tribune";
import { TribuneStar } from "@/components/tribune/tribune-provider";
import { EmptyState } from "@/components/ui/states";
import { api } from "@/lib/api";
import { splitTeamEvents } from "@/lib/events";
import { initLocale, t } from "@/lib/i18n";
import { isTribuneEmpty, type Tribune } from "@/lib/tribune";
import { getTribune } from "@/lib/tribune-server";
import type { NewsItem, SportEvent, Team } from "@/lib/types";

export const dynamic = "force-dynamic";

const MAX_TEAMS = 12;
const MAX_ITEMS = 24;
const TEAM_EVENTS = 100;
const NEWS_TEAMS = 4;
const NEWS_PER_TEAM = 4;
const NEWS_SHOWN = 6;

export async function generateMetadata(): Promise<Metadata> {
  await initLocale();
  return { title: t().tribune.title };
}

/** Fetches each id; a record that no longer exists is skipped, not an error page. */
async function loadAll<T>(ids: number[], load: (id: number) => Promise<T>): Promise<T[]> {
  const settled = await Promise.allSettled(ids.map(load));
  return settled.flatMap((r) => (r.status === "fulfilled" ? [r.value] : []));
}

function Heading({ id, children }: { id: string; children: React.ReactNode }) {
  return (
    <h2 id={id} className="mb-3 text-lg font-bold">
      {children}
    </h2>
  );
}

export default async function TribunePage() {
  await initLocale();
  const tribune = await getTribune();
  return (
    <>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-4xl leading-none font-bold tracking-tight uppercase sm:text-5xl">
            <SplitWords text={t().tribune.title} />
          </h1>
          <p className="text-muted-foreground mt-1.5 text-sm">{t().tribune.subtitle}</p>
          <p className="text-muted-foreground mt-0.5 text-xs">{t().tribune.device}</p>
        </div>
        {!isTribuneEmpty(tribune) ? <ClearTribune /> : null}
      </div>
      {isTribuneEmpty(tribune) ? (
        <EmptyState title={t().tribune.emptyTitle} body={t().tribune.emptyBody}>
          <Link href="/" className="text-primary mt-2 text-sm font-medium underline">
            {t().nav.home}
          </Link>
        </EmptyState>
      ) : (
        <div className="space-y-8">
          <Suspense fallback={<EventCardsSkeleton cards={1} />}>
            <Matches ids={tribune.matches} />
          </Suspense>
          <Suspense fallback={<EventCardsSkeleton cards={1} />}>
            <Teams ids={tribune.teams} />
          </Suspense>
          <Suspense fallback={null}>
            <Leagues ids={tribune.competitions} />
          </Suspense>
          <Suspense fallback={null}>
            <Drivers ids={tribune.players} />
          </Suspense>
          <Suspense fallback={null}>
            <News tribune={tribune} />
          </Suspense>
        </div>
      )}
    </>
  );
}

async function Matches({ ids }: { ids: number[] }) {
  if (ids.length === 0) return null;
  const events = (await loadAll(ids.slice(0, MAX_ITEMS), api.event)).sort((a, b) =>
    a.start_time.localeCompare(b.start_time),
  );
  if (events.length === 0) return null;
  return (
    <section>
      <EventCard title={t().tribune.matches} events={events} showRound heading="h2" />
    </section>
  );
}

function MiniEvent({ label, event }: { label: string; event?: SportEvent }) {
  return (
    <div>
      <p className="text-muted-foreground px-3 pt-2 text-[11px] font-bold uppercase">
        {label}
      </p>
      {event ? (
        <ul>
          <EventItem event={event} />
        </ul>
      ) : (
        <p className="text-muted-foreground px-3 pb-2 text-sm">—</p>
      )}
    </div>
  );
}

async function TeamCard({ team }: { team: Team }) {
  const events = await api
    .teamEvents(team.id, { pageSize: TEAM_EVENTS })
    .then((page) => page.items)
    .catch(() => [] as SportEvent[]);
  const { recent, upcoming } = splitTeamEvents(events, 1);
  return (
    <article className="bg-card overflow-hidden rounded-xl border">
      <header className="flex items-center gap-3 border-b px-3 py-2.5">
        <TeamBadge team={team} size="md" />
        <Link
          href={`/teams/${team.id}`}
          className="min-w-0 flex-1 truncate font-semibold hover:underline"
        >
          {team.name}
        </Link>
        <TribuneStar kind="teams" id={team.id} name={team.name} />
      </header>
      <div className="divide-y">
        <MiniEvent label={t().tribune.upcoming} event={upcoming[0]} />
        <MiniEvent label={t().tribune.recent} event={recent[0]} />
      </div>
    </article>
  );
}

async function Teams({ ids }: { ids: number[] }) {
  if (ids.length === 0) return null;
  const teams = await loadAll(ids.slice(0, MAX_TEAMS), api.team);
  if (teams.length === 0) return null;
  return (
    <section aria-labelledby="my-teams">
      <Heading id="my-teams">{t().tribune.teams}</Heading>
      <div className="grid gap-4 lg:grid-cols-2">
        {teams.map((team) => (
          <TeamCard key={team.id} team={team} />
        ))}
      </div>
    </section>
  );
}

async function Leagues({ ids }: { ids: number[] }) {
  if (ids.length === 0) return null;
  const leagues = await loadAll(ids.slice(0, MAX_ITEMS), (id) =>
    api.competition(String(id)),
  );
  if (leagues.length === 0) return null;
  return (
    <section aria-labelledby="my-leagues">
      <Heading id="my-leagues">{t().tribune.competitions}</Heading>
      <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {leagues.map((c) => (
          <li
            key={c.id}
            className="bg-card lift relative flex items-center gap-3 rounded-xl border p-3"
          >
            <TeamBadge team={c} size="md" variant="competition" />
            <Link
              href={competitionHref(c)}
              className="min-w-0 flex-1 after:absolute after:inset-0"
            >
              <span className="block truncate font-semibold">{c.name}</span>
              <span className="text-muted-foreground block truncate text-xs">
                {c.country}
              </span>
            </Link>
            <TribuneStar
              kind="competitions"
              id={c.id}
              name={c.name}
              className="relative z-10"
            />
          </li>
        ))}
      </ul>
    </section>
  );
}

async function Drivers({ ids }: { ids: number[] }) {
  if (ids.length === 0) return null;
  const players = await loadAll(ids.slice(0, MAX_ITEMS), api.player);
  if (players.length === 0) return null;
  return (
    <section aria-labelledby="my-drivers">
      <Heading id="my-drivers">{t().tribune.drivers}</Heading>
      <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {players.map((p) => {
          const number = typeof p.extra.number === "string" ? p.extra.number : null;
          return (
            <li
              key={p.id}
              className="bg-card lift relative flex items-center gap-3 rounded-xl border p-3"
            >
              <span
                aria-hidden
                className="bg-muted num inline-flex size-9 shrink-0 items-center justify-center rounded-lg border text-xs font-bold"
              >
                {number ?? "—"}
              </span>
              <Link
                href={`/players/${p.id}`}
                className="min-w-0 flex-1 after:absolute after:inset-0"
              >
                <span className="block truncate font-semibold">{p.name}</span>
                <span className="text-muted-foreground block truncate text-xs">
                  {p.team?.name ?? p.nationality}
                </span>
              </Link>
              <TribuneStar
                kind="players"
                id={p.id}
                name={p.name}
                className="relative z-10"
              />
            </li>
          );
        })}
      </ul>
    </section>
  );
}

/** Newest stories tagged with the first few favourite teams, without duplicates. */
async function News({ tribune }: { tribune: Tribune }) {
  const queries = [
    ...tribune.teams
      .slice(0, NEWS_TEAMS)
      .map((team) => api.news({ team, pageSize: NEWS_PER_TEAM })),
    ...tribune.players
      .slice(0, NEWS_TEAMS)
      .map((player) => api.news({ player, pageSize: NEWS_PER_TEAM })),
  ];
  if (queries.length === 0) return null;
  const pages = await Promise.allSettled(queries);
  const seen = new Set<number>();
  const items: NewsItem[] = pages
    .flatMap((p) => (p.status === "fulfilled" ? p.value.items : []))
    .filter((item) => !seen.has(item.id) && seen.add(item.id))
    .sort((a, b) => b.published_at.localeCompare(a.published_at))
    .slice(0, NEWS_SHOWN);
  if (items.length === 0) return null;
  return (
    <section aria-labelledby="my-news">
      <Heading id="my-news">{t().tribune.forYouNews}</Heading>
      <NewsFeed items={items} />
    </section>
  );
}
