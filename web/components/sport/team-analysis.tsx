import Link from "next/link";
import { EventItem } from "@/components/sport/event-item";
import { FORM_STYLES } from "@/components/sport/standings-table";
import { TeamBadge } from "@/components/sport/team-badge";
import { tr } from "@/lib/i18n/tr";
import type { SportTemplate } from "@/lib/sports";
import type {
  FormEntry,
  HeadToHead,
  MatchResult,
  SplitStats,
  TeamAnalysis,
} from "@/lib/types";
import { cn } from "@/lib/utils";

type AnalysisRules = NonNullable<SportTemplate["analysis"]>;

const PERCENT = 100;
const CARD = "bg-card overflow-hidden rounded-lg border";
const CARD_TITLE =
  "bg-muted/60 border-b px-3 py-2 font-display text-lg font-semibold tracking-wide uppercase";

function pct(value: number): string {
  return `%${Math.round(value * PERCENT)}`;
}

function score(entry: FormEntry): string {
  return `${entry.scored}-${entry.conceded}`;
}

/** Oldest on the left, newest on the right, like a form guide. */
export function FormStrip({ form }: { form: FormEntry[] }) {
  return (
    <ol className="flex flex-wrap gap-1">
      {[...form].reverse().map((entry) => (
        <li key={entry.event_id}>
          <Link
            href={`/teams/${entry.opponent.id}`}
            title={`${tr.analysis.resultNames[entry.result]} · ${score(entry)} · ${entry.opponent.name}`}
            className={cn(
              "inline-flex size-8 items-center justify-center rounded-md text-xs font-bold",
              FORM_STYLES[entry.result],
            )}
          >
            <span aria-hidden>{tr.analysis.results[entry.result]}</span>
            <span className="sr-only">
              {`${tr.analysis.resultNames[entry.result]}, ${score(entry)}, ${entry.opponent.name}`}
            </span>
          </Link>
        </li>
      ))}
    </ol>
  );
}

function streakText(streak: string | null): string | null {
  if (!streak) return null;
  const kind = streak[0] as MatchResult;
  const length = Number(streak.slice(1));
  return tr.analysis.streaks[kind]?.(length) ?? null;
}

function SplitRow({
  label,
  stats,
  rules,
}: {
  label: string;
  stats: SplitStats;
  rules: AnalysisRules;
}) {
  return (
    <tr>
      <th scope="row" className="px-3 py-2 text-left font-medium">
        {label}
      </th>
      <td className="px-2 py-2 text-right">{stats.played}</td>
      <td className="px-2 py-2 text-right">{stats.won}</td>
      {rules.draws ? <td className="px-2 py-2 text-right">{stats.drawn}</td> : null}
      <td className="px-2 py-2 text-right">{stats.lost}</td>
      <td className="px-2 py-2 text-right">{stats.avg_scored.toFixed(1)}</td>
      <td className="px-2 py-2 text-right">{stats.avg_conceded.toFixed(1)}</td>
      <td className="px-3 py-2 text-right font-semibold">{pct(stats.win_pct)}</td>
    </tr>
  );
}

/** Home vs away win rate as two labelled bars. */
function HomeAwayBars({ home, away }: { home: SplitStats; away: SplitStats }) {
  const bars: [string, SplitStats][] = [
    [tr.analysis.home, home],
    [tr.analysis.away, away],
  ];
  return (
    <div className="space-y-2 px-3 py-3">
      {bars.map(([label, stats]) => (
        <div key={label} className="flex items-center gap-3 text-sm">
          <span className="w-20 shrink-0">{label}</span>
          <span className="bg-muted h-3 flex-1 overflow-hidden rounded-full">
            <span
              className="bg-primary block h-full rounded-full"
              style={{ width: `${Math.round(stats.win_pct * PERCENT)}%` }}
            />
          </span>
          <span className="num w-12 text-right font-semibold">{pct(stats.win_pct)}</span>
        </div>
      ))}
    </div>
  );
}

function Highlight({ label, entry }: { label: string; entry: FormEntry | null }) {
  if (!entry) return null;
  return (
    <div className="flex items-center justify-between gap-2 px-3 py-2 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <Link
        href={`/teams/${entry.opponent.id}`}
        className="flex items-center gap-2 font-medium hover:underline"
      >
        <span className="num font-bold">{score(entry)}</span>
        <TeamBadge team={entry.opponent} size="sm" />
        {tr.analysis.vs(entry.opponent.short_name ?? entry.opponent.name)}
      </Link>
    </div>
  );
}

export function TeamAnalysisPanel({
  analysis,
  rules,
}: {
  analysis: TeamAnalysis;
  rules: AnalysisRules;
}) {
  if (analysis.form.length === 0) return null;
  const { form_stats: recent } = analysis;
  const streak = streakText(analysis.streak);
  return (
    <section aria-labelledby="analysis" className="mt-8">
      <h2
        id="analysis"
        className="font-display text-primary mb-3 text-2xl font-semibold uppercase"
      >
        {tr.analysis.title}
      </h2>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className={CARD}>
          <h3 className={CARD_TITLE}>{tr.analysis.lastN(analysis.form.length)}</h3>
          <div className="space-y-3 px-3 py-3">
            <FormStrip form={analysis.form} />
            <p className="num text-sm">
              <span className="font-semibold">
                {rules.draws
                  ? tr.analysis.h2hSummary(recent.won, recent.drawn, recent.lost)
                  : `${recent.won}G · ${recent.lost}M`}
              </span>
              {streak ? <span className="text-muted-foreground"> · {streak}</span> : null}
            </p>
          </div>
          <div className="divide-y border-t">
            <Highlight label={tr.analysis.biggestWin} entry={analysis.biggest_win} />
            <Highlight label={tr.analysis.biggestLoss} entry={analysis.biggest_loss} />
          </div>
        </div>
        <div className={CARD}>
          <h3 className={CARD_TITLE}>
            {analysis.season ? tr.analysis.season(analysis.season) : tr.analysis.overall}
          </h3>
          <HomeAwayBars home={analysis.home} away={analysis.away} />
          <div className="overflow-x-auto border-t">
            <table className="num w-full text-sm">
              <caption className="sr-only">{tr.analysis.title}</caption>
              <thead className="text-muted-foreground text-xs">
                <tr>
                  <th scope="col" className="px-3 py-2 text-left">
                    <span className="sr-only">{tr.analysis.overall}</span>
                  </th>
                  <th scope="col" className="px-2 py-2 text-right">
                    {tr.analysis.played}
                  </th>
                  <th scope="col" className="px-2 py-2 text-right">
                    {tr.analysis.won}
                  </th>
                  {rules.draws ? (
                    <th scope="col" className="px-2 py-2 text-right">
                      {tr.analysis.drawn}
                    </th>
                  ) : null}
                  <th scope="col" className="px-2 py-2 text-right">
                    {tr.analysis.lost}
                  </th>
                  <th
                    scope="col"
                    className="px-2 py-2 text-right"
                    title={tr.analysis.avgScored[rules.unit]}
                  >
                    +/M
                  </th>
                  <th
                    scope="col"
                    className="px-2 py-2 text-right"
                    title={tr.analysis.avgConceded[rules.unit]}
                  >
                    −/M
                  </th>
                  <th scope="col" className="px-3 py-2 text-right">
                    {tr.analysis.winPct}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                <SplitRow
                  label={tr.analysis.overall}
                  stats={analysis.overall}
                  rules={rules}
                />
                <SplitRow label={tr.analysis.home} stats={analysis.home} rules={rules} />
                <SplitRow label={tr.analysis.away} stats={analysis.away} rules={rules} />
              </tbody>
            </table>
          </div>
          <p className="text-muted-foreground border-t px-3 py-2 text-xs">
            +/M: {tr.analysis.avgScored[rules.unit]} · −/M:{" "}
            {tr.analysis.avgConceded[rules.unit]}
            {rules.cleanSheets
              ? ` · ${tr.analysis.cleanSheets}: ${analysis.overall.clean_sheets}`
              : null}
          </p>
        </div>
      </div>
    </section>
  );
}

export function HeadToHeadCard({
  h2h,
  rules,
  title,
}: {
  h2h: HeadToHead;
  rules: AnalysisRules;
  title: string;
}) {
  const s = h2h.summary;
  return (
    <section className={cn(CARD, "mt-4")}>
      <header className="bg-muted/60 flex flex-wrap items-baseline justify-between gap-2 border-b px-3 py-2">
        <h3 className="font-display text-lg font-semibold tracking-wide uppercase">
          {title}
        </h3>
        {s.played ? (
          <span className="num text-sm font-semibold">
            {rules.draws
              ? tr.analysis.h2hSummary(s.won, s.drawn, s.lost)
              : `${s.won}G · ${s.lost}M`}{" "}
            <span className="text-muted-foreground font-normal">
              ({s.scored}-{s.conceded})
            </span>
          </span>
        ) : null}
      </header>
      {h2h.matches.length ? (
        <ul className="divide-y">
          {h2h.matches.map((event) => (
            <EventItem key={event.id} event={event} showRound />
          ))}
        </ul>
      ) : (
        <p className="text-muted-foreground px-3 py-4 text-sm">{tr.analysis.h2hEmpty}</p>
      )}
    </section>
  );
}
