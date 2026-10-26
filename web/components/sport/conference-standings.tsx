import Link from "next/link";
import { TeamBadge } from "@/components/sport/team-badge";
import { tr } from "@/lib/i18n/tr";
import type { Standing } from "@/lib/types";
import { cn } from "@/lib/utils";

const CONFERENCES = ["East", "West"] as const;
const TH = "px-2 py-2 font-semibold";
const FORM_STYLES: Record<string, string> = {
  W: "bg-primary text-primary-foreground",
  L: "bg-accent text-accent-foreground",
};

const conferenceOf = (row: Standing) => String(row.extra.conference ?? "");
const rankOf = (row: Standing) => Number(row.extra.conference_rank ?? row.position);

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
            FORM_STYLES[r] ?? "bg-muted text-muted-foreground",
          )}
        >
          {r}
        </span>
      ))}
    </span>
  );
}

function pct(row: Standing): string {
  const value = Number(row.extra.win_pct);
  return Number.isFinite(value) ? value.toFixed(3).replace(/^0/, "") : "–";
}

/** NBA-style standings: one table per conference, ranked within the conference. */
export function ConferenceStandings({ rows }: { rows: Standing[] }) {
  return (
    <div className="grid gap-8 lg:grid-cols-2">
      {CONFERENCES.map((conference) => {
        const title = tr.conference[conference];
        const table = rows
          .filter((r) => conferenceOf(r) === conference)
          .sort((a, b) => rankOf(a) - rankOf(b));
        return (
          <section key={conference} aria-label={tr.conference.caption(title)}>
            <h2 className="font-display text-primary mb-2 text-2xl font-semibold uppercase">
              {title}
            </h2>
            <div
              className="bg-card overflow-x-auto rounded-lg border"
              tabIndex={0}
              role="region"
              aria-label={tr.conference.caption(title)}
            >
              <table className="num w-full min-w-[24rem] border-collapse text-sm">
                <caption className="sr-only">{tr.conference.caption(title)}</caption>
                <thead className="bg-muted/60 text-muted-foreground text-xs uppercase">
                  <tr>
                    <th scope="col" className={cn(TH, "w-10 text-center")}>
                      #
                    </th>
                    <th scope="col" className={cn(TH, "text-left")}>
                      {tr.standings.team}
                    </th>
                    <th scope="col" className={cn(TH, "text-right")}>
                      {tr.standings.played}
                    </th>
                    <th scope="col" className={cn(TH, "text-right")}>
                      {tr.standings.won}
                    </th>
                    <th scope="col" className={cn(TH, "text-right")}>
                      {tr.standings.lost}
                    </th>
                    <th scope="col" className={cn(TH, "text-right")}>
                      {tr.conference.winPct}
                    </th>
                    <th scope="col" className={cn(TH, "text-left")}>
                      {tr.conference.form}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {table.map((row) => (
                    <tr key={row.team?.id ?? row.position} className="hover:bg-muted/40">
                      <td className="px-2 py-2 text-center font-semibold">
                        {rankOf(row)}
                      </td>
                      <th scope="row" className="px-2 py-2 text-left font-medium">
                        {row.team ? (
                          <Link
                            href={`/teams/${row.team.id}`}
                            className="flex items-center gap-2 hover:underline"
                          >
                            <TeamBadge team={row.team} size="sm" />
                            <span className="truncate">{row.team.name}</span>
                          </Link>
                        ) : (
                          "—"
                        )}
                      </th>
                      <td className="px-2 py-2 text-right">{row.played}</td>
                      <td className="px-2 py-2 text-right">{row.won}</td>
                      <td className="px-2 py-2 text-right">{row.lost}</td>
                      <td className="px-2 py-2 text-right font-bold">{pct(row)}</td>
                      <td className="px-2 py-2">
                        <Form value={row.extra.form} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        );
      })}
      <p className="text-muted-foreground text-xs lg:col-span-2">
        {tr.conference.legend}
      </p>
    </div>
  );
}
