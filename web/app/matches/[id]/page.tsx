import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import {
  MatchHeader,
  MatchLineups,
  MatchSourceNote,
  MatchStats,
  MatchTimeline,
} from "@/components/match/match-parts";
import { PredictionRow } from "@/components/predictions/prediction-parts";
import { LiveRefresher } from "@/components/sport/live-refresher";
import { EmptyState } from "@/components/ui/states";
import { api } from "@/lib/api";
import { orNotFound, parseId } from "@/lib/api-helpers";
import { sideOf } from "@/lib/events";
import { initLocale, t } from "@/lib/i18n";
import type { MatchDetails, SportEvent } from "@/lib/types";

export const dynamic = "force-dynamic";

type Props = { params: Promise<{ id: string }> };

function matchTitle(event: SportEvent): string {
  const home = sideOf(event, "home")?.team?.name ?? "—";
  const away = sideOf(event, "away")?.team?.name ?? "—";
  return `${home} – ${away}`;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  await initLocale();
  const event = await api.event(parseId((await params).id)).catch(() => null);
  return { title: event ? matchTitle(event) : t().match.open };
}

export default async function MatchPage({ params }: Props) {
  await initLocale();
  const id = parseId((await params).id);
  // Existence is checked before anything streams so a missing match is a real HTTP 404.
  const event = await orNotFound(api.event(id));
  if (event.kind !== "match") notFound();

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <LiveRefresher active={event.status === "live"} />
      <Suspense fallback={<MatchHeader event={event} />}>
        <Details event={event} />
      </Suspense>
      {event.status === "scheduled" ? <PredictCard event={event} /> : null}
    </div>
  );
}

/** The prediction game's score boxes for an upcoming match. */
function PredictCard({ event }: { event: SportEvent }) {
  return (
    <section aria-labelledby="predict-this" className="bg-card rounded-xl border">
      <div className="flex items-center justify-between gap-3 border-b px-4 py-3">
        <h2 id="predict-this" className="font-display text-xl font-semibold uppercase">
          {t().predict.title}
        </h2>
        <Link href="/tahmin" className="text-primary text-sm font-medium hover:underline">
          {t().predict.mine}
        </Link>
      </div>
      <ul>
        <PredictionRow event={event} />
      </ul>
    </section>
  );
}

async function Details({ event }: { event: SportEvent }) {
  const details = await api.matchDetails(event.id).catch(() => null);
  return (
    <>
      <MatchHeader event={event} attendance={details?.attendance} />
      {details?.available ? (
        <Available details={details} event={event} />
      ) : (
        <Missing details={details} />
      )}
    </>
  );
}

function Available({ details, event }: { details: MatchDetails; event: SportEvent }) {
  return (
    <>
      <div className="grid gap-6 lg:grid-cols-2">
        <MatchTimeline incidents={details.incidents} />
        {details.stats.length ? <MatchStats stats={details.stats} /> : null}
      </div>
      <MatchLineups details={details} event={event} />
      <MatchSourceNote source={details.source} />
    </>
  );
}

function Missing({ details }: { details: MatchDetails | null }) {
  const reason = details?.reason ?? "unavailable";
  const body =
    reason === "unsupported"
      ? t().match.unsupported
      : reason === "not_started"
        ? t().match.notStarted
        : t().match.unavailable;
  return <EmptyState title={t().match.lineups} body={body} />;
}
