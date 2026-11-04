import Link from "next/link";
import { TeamBadge } from "@/components/sport/team-badge";
import { EmptyState } from "@/components/ui/states";
import { formatChance, likelyRange } from "@/lib/forecast";
import { intlLocale, t } from "@/lib/i18n";
import type { SeasonForecast, TeamForecast } from "@/lib/types";
import { cn } from "@/lib/utils";

/** Chances at or above this get the strong colour in the probability columns. */
const STRONG_CHANCE = 0.5;

function Chance({ value, tone }: { value: number; tone: "good" | "bad" }) {
  return (
    <td
      className={cn(
        "px-2 py-2 text-right tabular-nums",
        value >= STRONG_CHANCE
          ? tone === "good"
            ? "text-primary font-bold"
            : "text-live font-bold"
          : value > 0
            ? "text-foreground"
            : "text-muted-foreground",
      )}
    >
      {formatChance(value, intlLocale())}
    </td>
  );
}

/** One small square per finishing place, darker where the team is more likely to end up. */
function PlaceStrip({
  row,
  relegationFrom,
}: {
  row: TeamForecast;
  relegationFrom: number | null;
}) {
  const locale = intlLocale();
  const [lo, hi] = likelyRange(row.positions);
  return (
    <div className="flex items-center gap-px" aria-label={t().forecast.likely(lo, hi)}>
      {row.positions.map((p, i) => (
        <span
          key={i}
          title={t().forecast.place(i + 1, formatChance(p, locale))}
          className={cn(
            "h-4 w-2.5 rounded-[2px]",
            relegationFrom !== null && i + 1 >= relegationFrom ? "bg-live" : "bg-primary",
          )}
          // Square root lifts small but real chances so they stay visible.
          style={{ opacity: p > 0 ? 0.08 + 0.92 * Math.sqrt(p) : 0.04 }}
        />
      ))}
    </div>
  );
}

export function SeasonForecastView({ forecast }: { forecast: SeasonForecast }) {
  const m = t().forecast;
  if (!forecast.available) {
    const reason = forecast.reason ?? "unsupported";
    const title =
      reason === "finished"
        ? m.finished
        : reason === "not_started"
          ? m.notStarted
          : m.unsupported;
    return <EmptyState title={title} />;
  }
  const locale = intlLocale();
  const topLabel = forecast.top_kind === "europe" ? m.europe : m.top(forecast.top_spots);
  const relegationFrom = forecast.relegation_spots
    ? forecast.teams.length - forecast.relegation_spots + 1
    : null;
  const sims = new Intl.NumberFormat(locale).format(forecast.simulations);

  return (
    <section aria-labelledby="forecast-title" className="space-y-4">
      <div>
        <h2
          id="forecast-title"
          className="font-display text-primary text-2xl font-semibold uppercase"
        >
          {m.title}
        </h2>
        <p className="text-muted-foreground mt-1 max-w-3xl text-sm">
          {m.intro(sims, forecast.played, forecast.remaining)}
        </p>
      </div>

      <div className="bg-card overflow-x-auto rounded-lg border">
        <table className="w-full text-sm sm:min-w-[34rem]">
          <thead className="bg-muted/60 text-muted-foreground text-xs uppercase">
            <tr>
              <th scope="col" className="w-8 px-2 py-2 text-left">
                #
              </th>
              <th scope="col" className="px-2 py-2 text-left">
                {m.team}
              </th>
              <th
                scope="col"
                className="hidden px-2 py-2 text-right sm:table-cell"
                title={m.pointsLong}
              >
                {m.points}
              </th>
              <th
                scope="col"
                className="hidden px-2 py-2 text-right sm:table-cell"
                title={m.expectedLong}
              >
                {m.expected}
              </th>
              <th scope="col" className="px-2 py-2 text-right">
                {m.champion}
              </th>
              <th scope="col" className="px-2 py-2 text-right">
                {topLabel}
              </th>
              {relegationFrom ? (
                <th scope="col" className="px-2 py-2 text-right">
                  {m.relegation}
                </th>
              ) : null}
              <th scope="col" className="hidden px-2 py-2 text-left lg:table-cell">
                {m.distribution}
              </th>
              <th scope="col" className="hidden px-2 py-2 text-right sm:table-cell">
                {m.elo}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {forecast.teams.map((row, i) => (
              <tr key={row.team.id} className="hover:bg-muted/40">
                <td className="text-muted-foreground px-2 py-2 tabular-nums">{i + 1}</td>
                <td className="px-2 py-2">
                  <Link
                    href={`/teams/${row.team.id}`}
                    className="flex items-center gap-2 font-medium hover:underline"
                  >
                    <TeamBadge team={row.team} size="sm" />
                    {/* Phones get the short code so the chance columns fit. */}
                    <span className="sm:hidden">
                      {row.team.short_name ?? row.team.name}
                    </span>
                    <span className="hidden sm:inline">{row.team.name}</span>
                  </Link>
                </td>
                <td className="hidden px-2 py-2 text-right tabular-nums sm:table-cell">
                  {row.points}
                </td>
                <td className="hidden px-2 py-2 text-right font-semibold tabular-nums sm:table-cell">
                  {row.expected_points.toLocaleString(locale, {
                    maximumFractionDigits: 0,
                  })}
                </td>
                <Chance value={row.title} tone="good" />
                <Chance value={row.top} tone="good" />
                {relegationFrom ? (
                  <Chance value={row.relegation ?? 0} tone="bad" />
                ) : null}
                <td className="hidden px-2 py-2 lg:table-cell">
                  <PlaceStrip row={row} relegationFrom={relegationFrom} />
                </td>
                <td className="text-muted-foreground hidden px-2 py-2 text-right tabular-nums sm:table-cell">
                  {Math.round(row.elo)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-muted-foreground hidden text-xs lg:block">{m.legend}</p>

      <details className="bg-card rounded-lg border p-4 text-sm">
        <summary className="cursor-pointer font-semibold">{m.how}</summary>
        <ol className="text-muted-foreground mt-3 list-decimal space-y-2 pl-5">
          {m.howSteps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
        <p className="text-muted-foreground mt-3 text-xs">{m.caveat}</p>
      </details>
    </section>
  );
}
