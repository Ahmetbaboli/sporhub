import { SeriesChart } from "@/components/charts/series-chart";
import { api } from "@/lib/api";
import { tr } from "@/lib/i18n/tr";
import { driverPoints, driverPositions } from "@/lib/series";
import type { Player, PlayerSeasonStats } from "@/lib/types";

const RACE_SPORT = "formula-1";
const EVENTS_FETCH_SIZE = 100;
const MIN_CHART_POINTS = 2;
/** Tiles shown on the profile, in order; missing keys are skipped. */
const TILE_KEYS = [
  "goals",
  "assists",
  "played",
  "goals_per_match",
  "penalties",
  "race_points",
  "wins",
  "podiums",
  "poles",
  "best_finish",
  "avg_finish",
  "dnf",
] as const;
const DECIMAL_KEYS = new Set(["goals_per_match", "avg_finish"]);

function StatTiles({ sheet }: { sheet: PlayerSeasonStats }) {
  const labels = tr.compare.metrics as Record<string, string>;
  const tiles = TILE_KEYS.filter((k) => sheet.stats[k] !== undefined);
  return (
    <div className="bg-card overflow-hidden rounded-lg border">
      <p className="bg-muted/60 border-b px-3 py-2 text-xs">
        <span className="font-semibold">{sheet.competition.name}</span>
        <span className="text-muted-foreground"> · {sheet.season}</span>
      </p>
      <dl className="grid grid-cols-2 gap-px sm:grid-cols-4">
        {tiles.map((key) => (
          <div key={key} className="p-3">
            <dt className="text-muted-foreground text-xs font-semibold uppercase">
              {labels[key]}
            </dt>
            <dd className="num font-display mt-1 text-3xl leading-none font-bold">
              {DECIMAL_KEYS.has(key) ? sheet.stats[key].toFixed(2) : sheet.stats[key]}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

/** Season stat tiles for every sport that has them, plus race charts for drivers. */
export async function PlayerPerformance({ player }: { player: Player }) {
  const isDriver = player.team?.sport_slug === RACE_SPORT;
  const [stats, events] = await Promise.all([
    api.playerStats(player.id),
    isDriver ? api.playerEvents(player.id, { pageSize: EVENTS_FETCH_SIZE }) : null,
  ]);
  const positions = events ? driverPositions(events.items, player.id) : [];
  const points = events ? driverPoints(events.items, player.id) : [];
  if (stats.items.length === 0 && positions.length < MIN_CHART_POINTS) return null;

  return (
    <section aria-labelledby="season-stats" className="mt-8 space-y-4">
      <h2
        id="season-stats"
        className="font-display text-primary text-2xl font-semibold uppercase"
      >
        {tr.charts.seasonStats}
      </h2>
      {stats.items.map((sheet) => (
        <StatTiles key={`${sheet.competition.id}-${sheet.season}`} sheet={sheet} />
      ))}
      {positions.length >= MIN_CHART_POINTS ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <SeriesChart
            title={tr.charts.positionTitle}
            description={tr.charts.positionDescription}
            data={positions}
            valueLabel={tr.charts.position}
            xLabel={tr.charts.race}
            format="position"
          />
          <SeriesChart
            title={tr.charts.driverPointsTitle}
            description={tr.charts.driverPointsDescription}
            data={points}
            valueLabel={tr.charts.points}
            xLabel={tr.charts.race}
          />
        </div>
      ) : null}
    </section>
  );
}
