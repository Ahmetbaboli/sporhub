import { ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { LeagueTabs } from "@/components/home/league-tabs";
import { CountUp, Reveal } from "@/components/motion/motion";
import { competitionHref } from "@/components/sport/event-list";
import { TeamBadge } from "@/components/sport/team-badge";
import { zoneColor } from "@/components/sport/standings-table";
import { api } from "@/lib/api";
import { t } from "@/lib/i18n";
import type { Competition, LeaderRow, Standing } from "@/lib/types";
import { cn } from "@/lib/utils";

/** Leagues shown in the home widgets, in this order (those the API has). */
export const HUB_LEAGUES = [
  "super-lig",
  "premier-league",
  "primera-division",
  "serie-a",
  "bundesliga",
  "ligue-1",
];
const MINI_TABLE_ROWS = 8;
const SCORERS_ROWS = 6;

async function hubLeagues(): Promise<Competition[]> {
  const all = await api
    .competitions("football")
    .then((p) => p.items)
    .catch(() => []);
  return HUB_LEAGUES.flatMap((slug) => all.filter((c) => c.slug === slug));
}

function WidgetShell({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Reveal>
      <section aria-label={title} className="glass overflow-hidden rounded-xl">
        <h2 className="px-3 pt-3 text-lg font-bold">{title}</h2>
        {children}
      </section>
    </Reveal>
  );
}

function MoreLink({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      className="text-primary flex items-center justify-end gap-1 border-t px-3 py-2 text-xs font-semibold hover:underline"
    >
      {label}
      <ArrowUpRight className="pill-arrow size-3.5" aria-hidden />
    </Link>
  );
}

function MiniTable({ rows, href }: { rows: Standing[]; href: string }) {
  return (
    <>
      <table className="num w-full text-sm">
        <caption className="sr-only">{t().standings.caption}</caption>
        <thead className="text-muted-foreground text-[11px] uppercase">
          <tr>
            <th scope="col" className="w-8 py-1.5 pl-3 text-left font-semibold">
              #
            </th>
            <th scope="col" className="py-1.5 text-left font-semibold">
              {t().standings.team}
            </th>
            <th scope="col" className="w-8 py-1.5 text-right font-semibold">
              {t().standings.played}
            </th>
            <th scope="col" className="w-9 py-1.5 text-right font-semibold">
              {t().standings.goalDifference}
            </th>
            <th scope="col" className="w-10 py-1.5 pr-3 text-right font-semibold">
              {t().standings.points}
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, MINI_TABLE_ROWS).map((row) => {
            const color = zoneColor(row);
            const gd = row.extra.goal_difference;
            return (
              <tr key={row.position} className="hover:bg-muted/40 border-t">
                <td className="relative py-1.5 pl-3 font-semibold">
                  {color ? (
                    <span
                      aria-hidden
                      className="absolute top-1 bottom-1 left-0 w-[3px] rounded-r"
                      style={{ background: color }}
                    />
                  ) : null}
                  {row.position}
                </td>
                <th scope="row" className="py-1.5 text-left font-medium">
                  {row.team ? (
                    <Link
                      href={`/teams/${row.team.id}`}
                      className="flex min-w-0 items-center gap-2 hover:underline"
                    >
                      <TeamBadge team={row.team} size="sm" />
                      <span className="truncate">{row.team.name}</span>
                    </Link>
                  ) : null}
                </th>
                <td className="py-1.5 text-right">{row.played}</td>
                <td className="text-muted-foreground py-1.5 text-right">
                  {typeof gd === "number" ? (gd > 0 ? `+${gd}` : gd) : "–"}
                </td>
                <td className="py-1.5 pr-3 text-right font-bold">{row.points}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <MoreLink href={href} label={t().hub.fullTable} />
    </>
  );
}

/** Mackolik-style mini standings with a league switcher. */
export async function StandingsWidget() {
  const leagues = await hubLeagues();
  const tables = await Promise.all(
    leagues.map(async (c) => ({
      c,
      rows: await api
        .standings(c.slug)
        .then((p) => p.items)
        .catch(() => [] as Standing[]),
    })),
  );
  const tabs = tables
    .filter(({ rows }) => rows.length > 0)
    .map(({ c, rows }) => ({
      id: c.slug,
      label: c.name,
      badge: <TeamBadge team={c} size="sm" variant="competition" />,
      panel: <MiniTable rows={rows} href={`${competitionHref(c)}?tab=standings`} />,
    }));
  if (tabs.length === 0) return null;
  return (
    <WidgetShell title={t().hub.standings}>
      <LeagueTabs tabs={tabs} label={t().hub.pickLeague} />
    </WidgetShell>
  );
}

function ScorerList({ rows, href }: { rows: LeaderRow[]; href: string }) {
  if (rows.length === 0) {
    return <p className="text-muted-foreground px-3 py-4 text-sm">{t().hub.noScorers}</p>;
  }
  const top = rows[0]?.value ?? 1;
  return (
    <>
      <ol>
        {rows.slice(0, SCORERS_ROWS).map((row) => (
          <li
            key={`${row.rank}-${row.player?.id}`}
            className="flex items-center gap-2.5 border-t px-3 py-2"
          >
            <span
              className={cn("num w-5 text-sm font-bold", row.rank === 1 && "text-accent")}
            >
              {row.rank}
            </span>
            {row.player?.team ? <TeamBadge team={row.player.team} size="sm" /> : null}
            <span className="min-w-0 flex-1">
              {row.player ? (
                <Link
                  href={`/players/${row.player.id}`}
                  className="block truncate text-sm font-medium hover:underline"
                >
                  {row.player.name}
                </Link>
              ) : null}
              <span
                aria-hidden
                className="bg-muted mt-1 block h-1 overflow-hidden rounded-full"
              >
                <span
                  className="bg-primary block h-full rounded-full"
                  style={{ width: `${(row.value / top) * 100}%` }}
                />
              </span>
            </span>
            <span className="num text-sm font-bold">
              {row.value}
              <span className="sr-only"> {t().hub.goals}</span>
            </span>
          </li>
        ))}
      </ol>
      <MoreLink href={href} label={t().hub.allScorers} />
    </>
  );
}

/** Top scorers per league (only leagues whose source provides player goals). */
export async function ScorersWidget() {
  const leagues = await hubLeagues();
  const boards = await Promise.all(
    leagues.map(async (c) => ({
      c,
      rows:
        (await api
          .competitionStats(c.slug)
          .then((s) => s.leaders.find((b) => b.key === "goals")?.rows)
          .catch(() => undefined)) ?? [],
    })),
  );
  const tabs = boards
    .filter(({ rows }) => rows.length > 0)
    .map(({ c, rows }) => ({
      id: c.slug,
      label: c.name,
      badge: <TeamBadge team={c} size="sm" variant="competition" />,
      panel: <ScorerList rows={rows} href={`${competitionHref(c)}?tab=stats`} />,
    }));
  if (tabs.length === 0) return null;
  return (
    <WidgetShell title={t().hub.scorers}>
      <LeagueTabs tabs={tabs} label={t().hub.pickLeague} />
    </WidgetShell>
  );
}

/** Nerova-style logo wall: every league we carry, with its crest. */
export async function LeagueWall() {
  const sports = ["football", "basketball", "formula-1"];
  const lists = await Promise.all(
    sports.map((s) =>
      api
        .competitions(s)
        .then((p) => p.items)
        .catch(() => [] as Competition[]),
    ),
  );
  const leagues = lists.flat();
  if (leagues.length === 0) return null;
  return (
    <Reveal className="mt-10">
      <section aria-labelledby="league-wall">
        <h2 id="league-wall" className="mb-3 text-lg font-bold">
          {t().hub.leagueWall}
        </h2>
        <ul className="glass grid grid-cols-2 overflow-hidden rounded-2xl sm:grid-cols-3 lg:grid-cols-6">
          {leagues.map((c) => (
            <li key={c.id} className="border-border/60 -mt-px -ml-px border-t border-l">
              <Link
                href={competitionHref(c)}
                className="group hover:bg-muted/40 flex h-full items-center gap-2.5 px-4 py-4 transition-colors duration-200"
              >
                <span className="transition-transform duration-200 group-hover:scale-110">
                  <TeamBadge team={c} size="md" variant="competition" />
                </span>
                <span className="min-w-0">
                  <span className="block truncate text-sm font-semibold">{c.name}</span>
                  <span className="text-muted-foreground block truncate text-xs">
                    {c.country}
                  </span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </Reveal>
  );
}

/** A band of real counts from the API (no invented numbers). */
export async function StatsBand({ todayCount }: { todayCount: number }) {
  const [football, basketball, f1, news] = await Promise.all([
    api.competitions("football").catch(() => null),
    api.competitions("basketball").catch(() => null),
    api.competitions("formula-1").catch(() => null),
    api.news({ pageSize: 1 }).catch(() => null),
  ]);
  const leagues = (football?.total ?? 0) + (basketball?.total ?? 0) + (f1?.total ?? 0);
  const stats = [
    { value: leagues, label: t().hub.statLeagues },
    { value: todayCount, label: t().hub.statToday },
    { value: news?.total ?? 0, label: t().hub.statNews },
  ].filter((s) => s.value > 0);
  if (stats.length === 0) return null;
  return (
    <ul className="mb-6 flex flex-wrap gap-x-8 gap-y-2">
      {stats.map((s) => (
        <li key={s.label} className="flex items-baseline gap-1.5">
          <CountUp
            value={s.value}
            className="num font-display text-3xl leading-none font-bold"
          />
          <span className="text-muted-foreground text-sm">{s.label}</span>
        </li>
      ))}
    </ul>
  );
}
