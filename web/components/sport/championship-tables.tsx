import Link from "next/link";
import { TeamBadge } from "@/components/sport/team-badge";
import { tr } from "@/lib/i18n/tr";
import type { Standing } from "@/lib/types";
import { cn } from "@/lib/utils";

const TH = "px-2 py-2 font-semibold";

function Table({
  caption,
  children,
  className,
}: {
  caption: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section aria-label={caption}>
      <h2 className="font-display text-primary mb-2 text-2xl font-semibold uppercase">
        {caption}
      </h2>
      <div
        className="bg-card overflow-x-auto rounded-lg border"
        tabIndex={0}
        role="region"
        aria-label={caption}
      >
        <table className={cn("num w-full border-collapse text-sm", className)}>
          <caption className="sr-only">{caption}</caption>
          {children}
        </table>
      </div>
    </section>
  );
}

/** Formula 1 championship: drivers' and constructors' tables (rows are told apart by `player`). */
export function ChampionshipTables({ rows }: { rows: Standing[] }) {
  const drivers = rows.filter((r) => r.player);
  const constructors = rows.filter((r) => !r.player && r.team);
  return (
    <div className="space-y-8">
      <Table caption={tr.championship.drivers} className="min-w-[28rem]">
        <thead className="bg-muted/60 text-muted-foreground text-xs uppercase">
          <tr>
            <th scope="col" className={cn(TH, "w-10 text-center")}>
              #
            </th>
            <th scope="col" className={cn(TH, "text-left")}>
              {tr.championship.driver}
            </th>
            <th scope="col" className={cn(TH, "text-left")}>
              {tr.championship.team}
            </th>
            <th scope="col" className={cn(TH, "text-right")}>
              {tr.championship.wins}
            </th>
            <th scope="col" className={cn(TH, "text-right")}>
              {tr.championship.points}
            </th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {drivers.map((row) => (
            <tr key={row.player!.id} className="hover:bg-muted/40">
              <td className="px-2 py-2 text-center font-semibold">{row.position}</td>
              <th scope="row" className="px-2 py-2 text-left font-medium">
                <Link href={`/players/${row.player!.id}`} className="hover:underline">
                  {row.player!.name}
                </Link>
              </th>
              <td className="px-2 py-2">
                {row.team ? (
                  <Link href={`/teams/${row.team.id}`} className="hover:underline">
                    {row.team.name}
                  </Link>
                ) : (
                  "–"
                )}
              </td>
              <td className="px-2 py-2 text-right">{row.won}</td>
              <td className="px-2 py-2 text-right text-base font-bold">{row.points}</td>
            </tr>
          ))}
        </tbody>
      </Table>

      <Table caption={tr.championship.constructors} className="min-w-[22rem]">
        <thead className="bg-muted/60 text-muted-foreground text-xs uppercase">
          <tr>
            <th scope="col" className={cn(TH, "w-10 text-center")}>
              #
            </th>
            <th scope="col" className={cn(TH, "text-left")}>
              {tr.championship.team}
            </th>
            <th scope="col" className={cn(TH, "text-right")}>
              {tr.championship.wins}
            </th>
            <th scope="col" className={cn(TH, "text-right")}>
              {tr.championship.points}
            </th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {constructors.map((row) => (
            <tr key={row.team!.id} className="hover:bg-muted/40">
              <td className="px-2 py-2 text-center font-semibold">{row.position}</td>
              <th scope="row" className="px-2 py-2 text-left font-medium">
                <Link
                  href={`/teams/${row.team!.id}`}
                  className="flex items-center gap-2 hover:underline"
                >
                  <TeamBadge team={row.team!} size="sm" />
                  {row.team!.name}
                </Link>
              </th>
              <td className="px-2 py-2 text-right">{row.won}</td>
              <td className="px-2 py-2 text-right text-base font-bold">{row.points}</td>
            </tr>
          ))}
        </tbody>
      </Table>
      <p className="text-muted-foreground text-xs">{tr.championship.legend}</p>
    </div>
  );
}
