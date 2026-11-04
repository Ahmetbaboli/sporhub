import type { Metadata } from "next";
import {
  PredictionHistory,
  PredictionRow,
  PredictionScoreboard,
} from "@/components/predictions/prediction-parts";
import { EmptyState } from "@/components/ui/states";
import { TabNav } from "@/components/ui/tab-nav";
import { api } from "@/lib/api";
import { groupByDay } from "@/lib/events";
import { formatDay } from "@/lib/format";
import { initLocale, intlLocale, t } from "@/lib/i18n";
import type { Competition, SportEvent } from "@/lib/types";

export const dynamic = "force-dynamic";

const WINDOW_DAYS = 7;
const DAY_MS = 86_400_000;
const EVENTS_PER_LEAGUE = 100;
/** Listed first when it has matches: the home league of most visitors. */
const PREFERRED_LEAGUE = "super-lig";

type Props = { searchParams: Promise<{ lig?: string }> };

export async function generateMetadata(): Promise<Metadata> {
  await initLocale();
  return { title: t().predict.title };
}

const isoDay = (ms: number) => new Date(ms).toISOString().slice(0, 10);

/** Football leagues with upcoming two-team matches in the next week (Süper Lig first). */
async function loadLeagues(): Promise<{ league: Competition; events: SportEvent[] }[]> {
  const now = Date.now();
  const comps = (await api.competitions("football").catch(() => null))?.items ?? [];
  const loaded = await Promise.all(
    comps.map(async (league) => {
      const page = await api
        .competitionEvents(league.slug, {
          status: ["scheduled"],
          from: isoDay(now),
          to: isoDay(now + WINDOW_DAYS * DAY_MS),
          pageSize: EVENTS_PER_LEAGUE,
        })
        .catch(() => null);
      const events = (page?.items ?? []).filter(
        (e) => e.kind === "match" && Date.parse(e.start_time) > now,
      );
      return { league, events };
    }),
  );
  return loaded
    .filter((l) => l.events.length > 0)
    .sort(
      (a, b) =>
        Number(b.league.slug === PREFERRED_LEAGUE) -
          Number(a.league.slug === PREFERRED_LEAGUE) ||
        a.league.name.localeCompare(b.league.name),
    );
}

export default async function PredictPage({ searchParams }: Props) {
  await initLocale();
  const wanted = (await searchParams).lig;
  const leagues = await loadLeagues();
  const current = leagues.find((l) => l.league.slug === wanted) ?? leagues[0];

  return (
    <>
      <h1 className="font-display text-4xl leading-none font-bold tracking-tight uppercase sm:text-5xl">
        {t().predict.title}
      </h1>
      <p className="text-muted-foreground mt-2 max-w-2xl text-sm">{t().predict.intro}</p>

      <div className="mt-5">
        <PredictionScoreboard />
      </div>

      <section aria-labelledby="predict-upcoming" className="mt-8">
        <h2
          id="predict-upcoming"
          className="font-display text-primary mb-3 text-2xl font-semibold uppercase"
        >
          {t().predict.upcoming}
        </h2>
        {current ? (
          <>
            <TabNav
              label={t().predict.leagues}
              active={current.league.slug}
              tabs={leagues.map(({ league }) => ({
                id: league.slug,
                label: league.name,
                href: `/tahmin?lig=${league.slug}`,
              }))}
            />
            <div className="space-y-4">
              {groupByDay(current.events).map(({ day, events }) => (
                <div key={day} className="bg-card overflow-hidden rounded-lg border">
                  <h3 className="bg-muted/60 border-b px-3 py-2 text-sm font-semibold capitalize">
                    {formatDay(day, undefined, intlLocale())}
                  </h3>
                  <ul className="divide-y">
                    {events.map((event) => (
                      <PredictionRow key={event.id} event={event} />
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </>
        ) : (
          <EmptyState title={t().predict.noLeagues} />
        )}
      </section>

      <section aria-labelledby="predict-mine" className="mt-8">
        <h2
          id="predict-mine"
          className="font-display text-primary mb-3 text-2xl font-semibold uppercase"
        >
          {t().predict.mine}
        </h2>
        <PredictionHistory />
      </section>
    </>
  );
}
