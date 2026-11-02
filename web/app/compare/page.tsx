import type { Metadata } from "next";
import { Suspense } from "react";
import {
  compareHref,
  Contenders,
  MetricList,
  type CompareSelection,
  type Pickable,
  PickList,
  SearchBox,
  type Side,
  TypeSwitch,
} from "@/components/compare/compare-parts";
import { TableSkeleton } from "@/components/sport/skeletons";
import { FormStrip, HeadToHeadCard } from "@/components/sport/team-analysis";
import { EmptyState } from "@/components/ui/states";
import { api } from "@/lib/api";
import { orNotFound } from "@/lib/api-helpers";
import {
  pairSheets,
  parseCompareType,
  playerMetrics,
  sharedEntry,
  teamMetrics,
} from "@/lib/compare";
import { tr } from "@/lib/i18n/tr";
import { templateFor } from "@/lib/sports";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { title: tr.compare.title };

const MIN_QUERY_LENGTH = 2;
const SUGGESTION_LIMIT = 20;

type Props = {
  searchParams: Promise<{ type?: string; a?: string; b?: string; q?: string }>;
};

function optionalId(value: string | undefined): number | undefined {
  return value && /^\d+$/.test(value) ? Number(value) : undefined;
}

interface Loaded {
  side: Side;
  sport: string | null;
  teamId: number | null;
}

async function loadSide(type: CompareSelection["type"], id: number): Promise<Loaded> {
  if (type === "teams") {
    const team = await orNotFound(api.team(id));
    return {
      side: {
        id,
        name: team.name,
        href: `/teams/${id}`,
        badge: team,
        subtitle: team.country,
      },
      sport: team.sport_slug,
      teamId: id,
    };
  }
  const player = await orNotFound(api.player(id));
  return {
    side: {
      id,
      name: player.name,
      href: `/players/${id}`,
      badge: player.team,
      subtitle: [player.position, player.team?.name].filter(Boolean).join(" · ") || null,
    },
    sport: player.team?.sport_slug ?? null,
    teamId: player.team?.id ?? null,
  };
}

export default async function ComparePage({ searchParams }: Props) {
  const params = await searchParams;
  const selection: CompareSelection = {
    type: parseCompareType(params.type),
    a: optionalId(params.a),
    b: optionalId(params.b),
    q: params.q?.trim() || undefined,
  };
  const a = selection.a ? await loadSide(selection.type, selection.a) : null;
  const b = selection.b && a ? await loadSide(selection.type, selection.b) : null;

  return (
    <>
      <h1 className="font-display mb-4 text-4xl font-bold tracking-tight uppercase">
        {tr.compare.title}
      </h1>
      <TypeSwitch active={selection.type} />
      {a && b ? (
        <Comparison selection={selection} a={a} b={b} />
      ) : (
        <Picker selection={selection} a={a} />
      )}
    </>
  );
}

async function Picker({
  selection,
  a,
}: {
  selection: CompareSelection;
  a: Loaded | null;
}) {
  const heading = a
    ? tr.compare.pickSecond(a.side.name)
    : tr.compare.pickFirst[selection.type];
  const hrefFor = (id: number) =>
    compareHref(
      a ? { type: selection.type, a: a.side.id, b: id } : { type: selection.type, a: id },
    );
  const query =
    selection.q && selection.q.length >= MIN_QUERY_LENGTH ? selection.q : null;
  return (
    <section aria-labelledby="picker">
      <h2
        id="picker"
        className="font-display text-primary mb-3 text-2xl font-semibold uppercase"
      >
        {heading}
      </h2>
      <SearchBox selection={selection} />
      <Suspense key={query ?? "suggestions"} fallback={<TableSkeleton rows={5} />}>
        {query ? (
          <SearchResultsList
            selection={selection}
            a={a}
            query={query}
            hrefFor={hrefFor}
          />
        ) : a ? (
          <Suggestions selection={selection} a={a} hrefFor={hrefFor} />
        ) : null}
      </Suspense>
    </section>
  );
}

async function SearchResultsList({
  selection,
  a,
  query,
  hrefFor,
}: {
  selection: CompareSelection;
  a: Loaded | null;
  query: string;
  hrefFor: (id: number) => string;
}) {
  const results = await api.search(query);
  const sameSport = (sport: string | null | undefined) => !a?.sport || sport === a.sport;
  const items: Pickable[] =
    selection.type === "teams"
      ? results.teams
          .filter((t) => t.id !== a?.side.id && sameSport(t.sport_slug))
          .map((t) => ({ id: t.id, name: t.name, team: t, detail: t.country }))
      : results.players
          .filter((p) => p.id !== a?.side.id && sameSport(p.team?.sport_slug))
          .map((p) => ({
            id: p.id,
            name: p.name,
            team: p.team,
            detail: p.team?.name ?? null,
          }));
  return <PickList title={tr.compare.results} items={items} hrefFor={hrefFor} />;
}

/** Same-table rivals (league/championship), or teammates when there is no shared table. */
async function Suggestions({
  selection,
  a,
  hrefFor,
}: {
  selection: CompareSelection;
  a: Loaded;
  hrefFor: (id: number) => string;
}) {
  const isTeams = selection.type === "teams";
  const entries = await (
    isTeams ? api.teamStandings(a.side.id) : api.playerStandings(a.side.id)
  ).catch(() => null);
  const competition = entries?.items[0]?.competition;
  let items: Pickable[] = [];
  if (competition) {
    const table = await api.standings(competition.slug);
    items = table.items.flatMap((row): Pickable[] => {
      const entity = isTeams ? (row.player ? null : row.team) : row.player;
      if (!entity || entity.id === a.side.id) return [];
      const badge = isTeams ? row.team : (row.team ?? row.player?.team ?? null);
      return [
        { id: entity.id, name: entity.name, team: badge, detail: `${row.position}.` },
      ];
    });
  } else if (!isTeams && a.teamId) {
    const team = await api.team(a.teamId);
    items = team.squad
      .filter((p) => p.id !== a.side.id)
      .map((p) => ({ id: p.id, name: p.name, team: null, detail: p.position }));
  }
  return (
    <PickList
      title={tr.compare.suggestions}
      items={items.slice(0, SUGGESTION_LIMIT)}
      hrefFor={hrefFor}
    />
  );
}

function Comparison({
  selection,
  a,
  b,
}: {
  selection: CompareSelection;
  a: Loaded;
  b: Loaded;
}) {
  if (a.side.id === b.side.id) return <EmptyState title={tr.compare.sameEntity} />;
  if (a.sport && b.sport && a.sport !== b.sport) {
    return <EmptyState title={tr.compare.differentSports} />;
  }
  return (
    <>
      <Contenders a={a.side} b={b.side} selection={selection} />
      <Suspense fallback={<TableSkeleton rows={6} />}>
        {selection.type === "teams" ? (
          <TeamComparison a={a} b={b} />
        ) : (
          <PlayerComparison a={a} b={b} />
        )}
      </Suspense>
    </>
  );
}

async function TeamComparison({ a, b }: { a: Loaded; b: Loaded }) {
  const rules = templateFor(a.sport ?? "").analysis;
  const [analysisA, analysisB, entriesA, entriesB, h2h] = await Promise.all([
    rules ? api.teamAnalysis(a.side.id).catch(() => null) : null,
    rules ? api.teamAnalysis(b.side.id).catch(() => null) : null,
    api.teamStandings(a.side.id),
    api.teamStandings(b.side.id),
    rules ? api.headToHead(a.side.id, b.side.id).catch(() => null) : null,
  ]);
  const metrics = teamMetrics(
    analysisA,
    analysisB,
    sharedEntry(entriesA.items, entriesB.items),
    rules,
  );
  return (
    <>
      <MetricList metrics={metrics} />
      {analysisA?.form.length || analysisB?.form.length ? (
        <section className="bg-card mt-4 rounded-lg border p-3">
          <h2 className="text-muted-foreground mb-2 text-center text-xs font-semibold uppercase">
            {tr.compare.formTitle}
          </h2>
          <div className="flex flex-wrap justify-between gap-3">
            <FormStrip form={analysisA?.form ?? []} />
            <FormStrip form={analysisB?.form ?? []} />
          </div>
        </section>
      ) : null}
      {h2h && rules ? (
        <HeadToHeadCard h2h={h2h} rules={rules} title={tr.analysis.h2hTitle} />
      ) : null}
    </>
  );
}

async function PlayerComparison({ a, b }: { a: Loaded; b: Loaded }) {
  const [statsA, statsB, entriesA, entriesB] = await Promise.all([
    api.playerStats(a.side.id),
    api.playerStats(b.side.id),
    api.playerStandings(a.side.id),
    api.playerStandings(b.side.id),
  ]);
  const [sheetA, sheetB] = pairSheets(statsA.items, statsB.items);
  const metrics = playerMetrics(
    sheetA,
    sheetB,
    sharedEntry(entriesA.items, entriesB.items),
  );
  const season = sheetA ?? sheetB;
  return (
    <>
      {season ? (
        <p className="text-muted-foreground mt-4 text-center text-xs">
          {season.competition.name} · {tr.compare.season} {season.season}
        </p>
      ) : null}
      <MetricList metrics={metrics} />
    </>
  );
}
