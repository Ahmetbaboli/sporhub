import Link from "next/link";
import { EventItem } from "@/components/sport/event-item";
import { TeamBadge } from "@/components/sport/team-badge";
import { EmptyState } from "@/components/ui/states";
import { tr } from "@/lib/i18n/tr";
import type { SportTemplate } from "@/lib/sports";
import type {
  CompetitionStats,
  LeaderCategory,
  LeaderRow,
  MatchSummary,
  RaceSummary,
  SeasonHistoryRow,
} from "@/lib/types";

type Unit = "goals" | "points";

const PERCENT = 100;
const RATE_KEYS = new Set(["best_attack", "best_defence", "avg_finish"]);
const PCT_KEYS = new Set(["home_win_pct", "away_win_pct"]);
const CARD = "bg-card overflow-hidden rounded-lg border";
const CARD_TITLE =
  "bg-muted/60 border-b px-3 py-2 font-display text-lg font-semibold tracking-wide uppercase";
const SECTION_TITLE = "font-display text-primary mb-3 text-2xl font-semibold uppercase";

export function boardTitle(key: string, unit: Unit): string {
  const label = (tr.stats.boards as Record<string, string | Record<Unit, string>>)[key];
  if (label === undefined) return key;
  return typeof label === "string" ? label : label[unit];
}

export function formatLeaderValue(key: string, value: number): string {
  if (PCT_KEYS.has(key)) return `%${Math.round(value * PERCENT)}`;
  if (RATE_KEYS.has(key)) return value.toFixed(2);
  return String(Math.round(value));
}

function pct(value: number): string {
  return `%${Math.round(value * PERCENT)}`;
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="p-3">
      <dt className="text-muted-foreground text-xs font-semibold uppercase">{label}</dt>
      <dd className="num font-display mt-1 text-3xl leading-none font-bold">{value}</dd>
    </div>
  );
}

function MatchSummaryCard({ summary, unit }: { summary: MatchSummary; unit: Unit }) {
  return (
    <div className={CARD}>
      <h3 className={CARD_TITLE}>{tr.stats.summary}</h3>
      <dl className="grid grid-cols-3 divide-x border-b">
        <Stat label={tr.stats.matches} value={summary.played} />
        <Stat label={tr.stats.total[unit]} value={summary.total_scored} />
        <Stat label={tr.stats.perMatch[unit]} value={summary.avg_per_match.toFixed(2)} />
      </dl>
      <OutcomeBar summary={summary} />
      <ul className="divide-y border-t">
        {summary.biggest_win ? (
          <SummaryEvent label={tr.stats.biggestWin} event={summary.biggest_win} />
        ) : null}
        {summary.highest_scoring ? (
          <SummaryEvent
            label={tr.stats.highestScoring[unit]}
            event={summary.highest_scoring}
          />
        ) : null}
      </ul>
    </div>
  );
}

function SummaryEvent({
  label,
  event,
}: {
  label: string;
  event: NonNullable<MatchSummary["biggest_win"]>;
}) {
  return (
    <li>
      <p className="text-muted-foreground px-3 pt-2 text-xs font-semibold uppercase">
        {label}
      </p>
      <ul>
        <EventItem event={event} showRound />
      </ul>
    </li>
  );
}

/** Home win / draw / away win shares as one stacked bar with a text legend. */
function OutcomeBar({ summary }: { summary: MatchSummary }) {
  const parts = [
    { label: tr.stats.homeWin, value: summary.home_win_pct, className: "bg-primary" },
    {
      label: tr.stats.draw,
      value: summary.draw_pct,
      className: "bg-muted-foreground/40",
    },
    { label: tr.stats.awayWin, value: summary.away_win_pct, className: "bg-accent" },
  ].filter((p) => p.value > 0);
  return (
    <div className="space-y-2 px-3 py-3">
      <div className="flex h-3 overflow-hidden rounded-full" aria-hidden>
        {parts.map((p) => (
          <span
            key={p.label}
            className={p.className}
            style={{ width: `${p.value * PERCENT}%` }}
          />
        ))}
      </div>
      <ul className="text-muted-foreground flex flex-wrap gap-x-4 gap-y-1 text-xs">
        {parts.map((p) => (
          <li key={p.label} className="flex items-center gap-1.5">
            <span className={`${p.className} size-2.5 rounded-full`} aria-hidden />
            {p.label}{" "}
            <span className="num text-foreground font-semibold">{pct(p.value)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function RaceSummaryCard({ summary }: { summary: RaceSummary }) {
  return (
    <div className={CARD}>
      <h3 className={CARD_TITLE}>{tr.stats.summary}</h3>
      <dl className="grid grid-cols-2 divide-x divide-y sm:grid-cols-4 sm:divide-y-0">
        <Stat label={tr.stats.races} value={summary.completed} />
        <Stat label={tr.stats.racesLeft} value={summary.scheduled} />
        <Stat label={tr.stats.winners} value={summary.distinct_winners} />
        <Stat label={tr.stats.poleToWin} value={summary.pole_to_win} />
      </dl>
    </div>
  );
}

function LeaderName({ row, subject }: { row: LeaderRow; subject: "player" | "team" }) {
  if (subject === "player" && row.player) {
    return (
      <span className="flex min-w-0 items-center gap-2">
        {row.team ? <TeamBadge team={row.team} size="sm" /> : null}
        <span className="min-w-0">
          <Link
            href={`/players/${row.player.id}`}
            className="font-medium hover:underline"
          >
            {row.player.name}
          </Link>
          {row.team ? (
            <span className="text-muted-foreground block truncate text-xs">
              {row.team.short_name ?? row.team.name}
            </span>
          ) : null}
        </span>
      </span>
    );
  }
  if (row.team) {
    return (
      <Link
        href={`/teams/${row.team.id}`}
        className="flex items-center gap-2 font-medium hover:underline"
      >
        <TeamBadge team={row.team} size="sm" />
        {row.team.name}
      </Link>
    );
  }
  return <span>—</span>;
}

export function LeaderBoard({
  category,
  unit,
  playedLabel,
}: {
  category: LeaderCategory;
  unit: Unit;
  playedLabel: (n: number) => string;
}) {
  const title = boardTitle(category.key, unit);
  return (
    <section className={CARD}>
      <h3 className={CARD_TITLE}>{title}</h3>
      <table className="num w-full text-sm">
        <caption className="sr-only">{title}</caption>
        <tbody className="divide-y">
          {category.rows.map((row) => (
            <tr key={`${row.rank}-${row.player?.id ?? row.team?.id}`}>
              <td className="text-muted-foreground w-10 px-3 py-2 text-right">
                {row.rank}
              </td>
              <td className="px-2 py-2">
                <LeaderName row={row} subject={category.subject} />
              </td>
              <td className="text-muted-foreground hidden px-2 py-2 text-right text-xs sm:table-cell">
                {row.played !== null ? playedLabel(row.played) : null}
              </td>
              <td className="w-16 px-3 py-2 text-right text-base font-bold">
                {formatLeaderValue(category.key, row.value)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function SeasonHistory({ rows }: { rows: SeasonHistoryRow[] }) {
  return (
    <section aria-labelledby="season-history">
      <h2 id="season-history" className={SECTION_TITLE}>
        {tr.stats.history}
      </h2>
      <ul className={`${CARD} divide-y`}>
        {rows.map(({ season, leader }) => {
          const subject = leader?.player ?? leader?.team;
          return (
            <li
              key={season.id}
              className="flex items-center justify-between gap-3 px-3 py-2"
            >
              <span className="font-semibold">
                {season.year_label}
                {season.is_current ? (
                  <span className="text-muted-foreground ml-2 text-xs font-normal">
                    {tr.stats.current}
                  </span>
                ) : null}
              </span>
              {subject && leader ? (
                <span className="flex items-center gap-2 text-sm">
                  <span className="text-muted-foreground text-xs uppercase">
                    {season.is_current ? tr.stats.leader : tr.stats.champion}
                  </span>
                  <Link
                    href={
                      leader.player ? `/players/${subject.id}` : `/teams/${subject.id}`
                    }
                    className="font-medium hover:underline"
                  >
                    {subject.name}
                  </Link>
                  <span className="num font-bold">{leader.points}</span>
                </span>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export function CompetitionStatsView({
  stats,
  template,
}: {
  stats: CompetitionStats;
  template: SportTemplate;
}) {
  const unit: Unit = template.analysis?.unit ?? "points";
  const players = stats.leaders.filter((c) => c.subject === "player");
  const teams = stats.leaders.filter((c) => c.subject === "team");
  const isRace = template.analysis === null;
  const playedLabel = isRace ? tr.stats.races_ : tr.stats.played;

  if (!stats.matches && !stats.races && stats.leaders.length === 0) {
    return <EmptyState title={tr.stats.empty} />;
  }
  return (
    <div className="space-y-8">
      {stats.matches ? <MatchSummaryCard summary={stats.matches} unit={unit} /> : null}
      {stats.races ? <RaceSummaryCard summary={stats.races} /> : null}
      <section aria-labelledby="player-leaders">
        <h2 id="player-leaders" className={SECTION_TITLE}>
          {isRace ? tr.stats.driverLeaders : tr.stats.playerLeaders}
        </h2>
        {players.length ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {players.map((c) => (
              <LeaderBoard
                key={c.key}
                category={c}
                unit={unit}
                playedLabel={playedLabel}
              />
            ))}
          </div>
        ) : (
          <EmptyState title={tr.stats.noPlayerStats} />
        )}
      </section>
      {teams.length ? (
        <section aria-labelledby="team-leaders">
          <h2 id="team-leaders" className={SECTION_TITLE}>
            {tr.stats.teamLeaders}
          </h2>
          <div className="grid gap-4 lg:grid-cols-2">
            {teams.map((c) => (
              <LeaderBoard
                key={c.key}
                category={c}
                unit={unit}
                playedLabel={playedLabel}
              />
            ))}
          </div>
        </section>
      ) : null}
      {stats.history.length ? <SeasonHistory rows={stats.history} /> : null}
    </div>
  );
}
