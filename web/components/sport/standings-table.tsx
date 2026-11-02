import Link from "next/link";
import { TeamBadge } from "@/components/sport/team-badge";
import { t } from "@/lib/i18n";
import type { Standing } from "@/lib/types";
import { cn } from "@/lib/utils";

const numeric = (value: unknown): number | null =>
  typeof value === "number" ? value : null;

function signed(value: number | null): string {
  if (value === null) return "–";
  return value > 0 ? `+${value}` : String(value);
}

export const FORM_STYLES: Record<string, string> = {
  W: "bg-primary text-primary-foreground",
  D: "bg-muted text-muted-foreground",
  L: "bg-accent text-accent-foreground",
};

function Form({ value }: { value: unknown }) {
  if (typeof value !== "string" || !value)
    return <span className="text-muted-foreground">–</span>;
  const results = value.split(",").filter(Boolean);
  return (
    <span className="inline-flex gap-0.5" aria-label={results.join(" ")}>
      {results.map((r, i) => (
        <span
          key={i}
          aria-hidden
          className={cn(
            "inline-flex size-4 items-center justify-center rounded-sm text-[9px] font-bold",
            FORM_STYLES[r] ?? FORM_STYLES.D,
          )}
        >
          {r}
        </span>
      ))}
    </span>
  );
}

const HEAD = "px-2 py-2 text-right font-semibold";

/** Wide table that scrolls inside its own container on narrow screens. */
export function StandingsTable({ rows }: { rows: Standing[] }) {
  return (
    <div
      className="bg-card overflow-x-auto rounded-lg border"
      tabIndex={0}
      role="region"
      aria-label={t().standings.caption}
    >
      <table className="num w-full min-w-[34rem] border-collapse text-sm">
        <caption className="sr-only">{t().standings.caption}</caption>
        <thead className="bg-muted/60 text-muted-foreground text-xs uppercase">
          <tr>
            <th scope="col" className="w-10 px-2 py-2 text-center font-semibold">
              <abbr title={t().standings.position} className="no-underline">
                #
              </abbr>
            </th>
            <th
              scope="col"
              className="bg-muted sticky left-0 px-2 py-2 text-left font-semibold"
            >
              {t().standings.team}
            </th>
            <th scope="col" className={HEAD}>
              {t().standings.played}
            </th>
            <th scope="col" className={HEAD}>
              {t().standings.won}
            </th>
            <th scope="col" className={HEAD}>
              {t().standings.drawn}
            </th>
            <th scope="col" className={HEAD}>
              {t().standings.lost}
            </th>
            <th scope="col" className={HEAD}>
              {t().standings.goalsFor}:{t().standings.goalsAgainst}
            </th>
            <th scope="col" className={HEAD}>
              {t().standings.goalDifference}
            </th>
            <th scope="col" className={cn(HEAD, "text-foreground")}>
              {t().standings.points}
            </th>
            <th scope="col" className="px-2 py-2 text-left font-semibold">
              {t().standings.form}
            </th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {rows.map((row) => {
            const gf = numeric(row.extra.goals_for);
            const ga = numeric(row.extra.goals_against);
            const name = row.team?.short_name
              ? row.team.name
              : (row.team?.name ?? row.player?.name ?? "—");
            return (
              <tr
                key={`${row.position}-${row.team?.id ?? row.player?.id}`}
                className="hover:bg-muted/40"
              >
                <td className="px-2 py-2 text-center font-semibold">{row.position}</td>
                <th
                  scope="row"
                  className="bg-card sticky left-0 px-2 py-2 text-left font-medium"
                >
                  {row.team ? (
                    <Link
                      href={`/teams/${row.team.id}`}
                      className="flex items-center gap-2 hover:underline"
                    >
                      <TeamBadge team={row.team} size="sm" />
                      <span className="max-w-40 truncate">{name}</span>
                    </Link>
                  ) : (
                    name
                  )}
                </th>
                <td className="px-2 py-2 text-right">{row.played}</td>
                <td className="px-2 py-2 text-right">{row.won}</td>
                <td className="px-2 py-2 text-right">{row.drawn}</td>
                <td className="px-2 py-2 text-right">{row.lost}</td>
                <td className="px-2 py-2 text-right">
                  {gf !== null && ga !== null ? `${gf}:${ga}` : "–"}
                </td>
                <td className="px-2 py-2 text-right">
                  {signed(numeric(row.extra.goal_difference))}
                </td>
                <td className="px-2 py-2 text-right text-base font-bold">{row.points}</td>
                <td className="px-2 py-2">
                  <Form value={row.extra.form} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="text-muted-foreground border-t px-3 py-2 text-xs">
        {t().standings.legend}
      </p>
    </div>
  );
}
