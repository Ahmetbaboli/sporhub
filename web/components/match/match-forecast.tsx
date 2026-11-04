import Link from "next/link";
import { api } from "@/lib/api";
import { formatChance } from "@/lib/forecast";
import { intlLocale, t } from "@/lib/i18n";
import type { MatchForecast, SportEvent } from "@/lib/types";

/** Pre-match win/draw/loss bar from the season's Elo ratings; nothing when not available. */
export function MatchForecastBar({
  event,
  forecast,
}: {
  event: SportEvent;
  forecast: MatchForecast | null;
}) {
  if (!forecast?.available || forecast.home == null || forecast.away == null) return null;
  const draw = forecast.draw ?? 0;
  const locale = intlLocale();
  const home = event.participants.find((p) => p.side === "home")?.team;
  const away = event.participants.find((p) => p.side === "away")?.team;
  const m = t().forecast;
  const parts = [
    { key: "home", label: home?.name ?? "—", value: forecast.home, bar: "bg-primary" },
    { key: "draw", label: m.draw, value: draw, bar: "bg-muted-foreground/40" },
    { key: "away", label: away?.name ?? "—", value: forecast.away, bar: "bg-accent" },
  ];
  return (
    <section aria-labelledby="match-forecast" className="bg-card rounded-xl border p-4">
      <div className="flex items-center justify-between gap-3">
        <h2 id="match-forecast" className="font-display text-xl font-semibold uppercase">
          {m.matchTitle}
        </h2>
        <Link
          href={`/${event.competition.sport_slug}/${event.competition.slug}?tab=forecast`}
          className="text-primary text-sm font-medium hover:underline"
        >
          {m.seeSeason}
        </Link>
      </div>
      <div className="mt-3 flex h-3 overflow-hidden rounded-full" aria-hidden>
        {parts.map((p) => (
          <span key={p.key} className={p.bar} style={{ width: `${p.value * 100}%` }} />
        ))}
      </div>
      <dl className="mt-2 grid grid-cols-3 gap-2 text-sm">
        {parts.map((p, i) => (
          <div
            key={p.key}
            className={i === 1 ? "text-center" : i === 2 ? "text-right" : ""}
          >
            <dt className="text-muted-foreground truncate text-xs">{p.label}</dt>
            <dd className="font-display text-2xl font-bold tabular-nums">
              {formatChance(p.value, locale)}
            </dd>
          </div>
        ))}
      </dl>
      {forecast.home_elo != null && forecast.away_elo != null ? (
        <p className="text-muted-foreground mt-2 text-xs">
          {m.matchNote(Math.round(forecast.home_elo), Math.round(forecast.away_elo))}
        </p>
      ) : null}
    </section>
  );
}

export async function MatchForecastSection({ event }: { event: SportEvent }) {
  const forecast = await api.matchForecast(event.id).catch(() => null);
  return <MatchForecastBar event={event} forecast={forecast} />;
}
