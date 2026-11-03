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
const HEX_COLOR = /^#[0-9a-f]{6}$/i;

/** The provider's own zone colour for a place (ESPN: CL, relegation…), if any. */
export function zoneColor(row: Standing): string | null {
  const color = row.extra.zone_color;
  return typeof color === "string" && HEX_COLOR.test(color) ? color : null;
}

function zoneName(raw: string): string {
  return (t().zones.names as Record<string, string>)[raw] ?? raw;
}

/** One entry per distinct zone, in table order. */
function zones(rows: Standing[]): { name: string; color: string }[] {
  const seen = new Map<string, string>();
  for (const row of rows) {
    const color = zoneColor(row);
    const name = typeof row.extra.zone === "string" ? row.extra.zone : null;
    if (color && name && !seen.has(name)) seen.set(name, color);
  }
  return [...seen].map(([name, color]) => ({ name: zoneName(name), color }));
}

/** Wide table that scrolls inside its own container on narrow screens. */
export function StandingsTable({ rows }: { rows: Standing[] }) {
  return (
    <div
      className="bg-card overflow-x-auto rounded-xl border"
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
                <td className="relative px-2 py-2 text-center font-semibold">
                  {zoneColor(row) ? (
                    <span
                      aria-hidden
                      className="absolute top-1.5 bottom-1.5 left-0 w-[3px] rounded-r"
                      style={{ background: zoneColor(row)! }}
                    />
                  ) : null}
                  {row.position}
                  {typeof row.extra.zone === "string" ? (
                    <span className="sr-only"> ({zoneName(row.extra.zone)})</span>
                  ) : null}
                </td>
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
      {zones(rows).length > 0 ? (
        <ul
          aria-label={t().zones.title}
          className="text-muted-foreground flex flex-wrap gap-x-4 gap-y-1 border-t px-3 py-2 text-xs"
        >
          {zones(rows).map((z) => (
            <li key={z.name} className="inline-flex items-center gap-1.5">
              <span
                aria-hidden
                className="size-2.5 rounded-sm"
                style={{ background: z.color }}
              />
              {z.name}
            </li>
          ))}
        </ul>
      ) : null}
      <p className="text-muted-foreground border-t px-3 py-2 text-xs">
        {t().standings.legend}
      </p>
    </div>
  );
}
