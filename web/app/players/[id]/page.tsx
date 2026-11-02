import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Freshness } from "@/components/layout/freshness";
import { CompareLink } from "@/components/compare/compare-link";
import { FavoriteToggle } from "@/components/account/favorite-toggle";
import { RelatedNews } from "@/components/news/related-news";
import { TableSkeleton } from "@/components/sport/skeletons";
import { PlayerPerformance } from "@/components/sport/player-performance";
import { TeamBadge } from "@/components/sport/team-badge";
import { api } from "@/lib/api";
import { orNotFound, parseId } from "@/lib/api-helpers";
import { formatDate } from "@/lib/format";
import { initLocale, intlLocale, t } from "@/lib/i18n";
import type { Messages } from "@/lib/i18n/tr";

export const dynamic = "force-dynamic";

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  await initLocale();
  const { id } = await params;
  const player = await api.player(parseId(id)).catch(() => null);
  return { title: player?.name ?? t().app.name };
}

/** Sport-specific profile facts stored in `player.extra` (shown only when present). */
const SPORT_FACTS: [string, keyof Messages["player"]][] = [
  ["number", "number"], // F1 permanent number
  ["code", "code"], // F1 three-letter code
  ["jersey_number", "number"], // basketball
  ["height", "height"],
  ["weight", "weight"],
];

export default async function PlayerPage({ params }: Props) {
  await initLocale();
  const player = await orNotFound(api.player(parseId((await params).id)));
  const birth =
    typeof player.extra.date_of_birth === "string" ? player.extra.date_of_birth : null;

  const facts: [string, React.ReactNode][] = [
    [t().player.position, player.position ?? t().player.unknown],
    [t().player.nationality, player.nationality ?? t().player.unknown],
    [t().player.birthDate, birth ? formatDate(birth, intlLocale()) : t().player.unknown],
    ...SPORT_FACTS.flatMap(([key, labelKey]): [string, React.ReactNode][] => {
      const label = t().player[labelKey];
      const value = player.extra[key];
      return typeof value === "string" || typeof value === "number"
        ? [[label, String(value)]]
        : [];
    }),
    [
      t().player.team,
      player.team ? (
        <Link
          href={`/teams/${player.team.id}`}
          className="flex items-center gap-2 hover:underline"
        >
          <TeamBadge team={player.team} size="sm" />
          {player.team.name}
        </Link>
      ) : (
        t().player.unknown
      ),
    ],
  ];

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-display text-4xl font-bold tracking-tight uppercase">
          {player.name}
        </h1>
        <div className="flex flex-wrap items-center gap-2">
          <CompareLink href={`/compare?type=players&a=${player.id}`} />
          <Suspense fallback={null}>
            <FavoriteToggle
              kind="players"
              id={player.id}
              name={player.name}
              returnTo={`/players/${player.id}`}
            />
          </Suspense>
        </div>
      </div>
      <dl className="bg-card mt-6 grid max-w-xl gap-px overflow-hidden rounded-lg border sm:grid-cols-2">
        {facts.map(([label, value]) => (
          <div key={label} className="p-4">
            <dt className="text-muted-foreground text-xs font-semibold uppercase">
              {label}
            </dt>
            <dd className="mt-1 text-base font-medium">{value}</dd>
          </div>
        ))}
      </dl>
      <Suspense fallback={null}>
        <RelatedNews kind="player" id={player.id} name={player.name} />
      </Suspense>
      <Suspense fallback={<TableSkeleton rows={4} />}>
        <PlayerPerformance player={player} />
      </Suspense>
      <Suspense fallback={null}>
        <Freshness sport={player.team?.sport_slug} />
      </Suspense>
    </>
  );
}
