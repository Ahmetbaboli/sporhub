import type { Metadata } from "next";
import Link from "next/link";
import { SearchForm } from "@/components/layout/search-form";
import { competitionHref } from "@/components/sport/event-list";
import { TeamBadge } from "@/components/sport/team-badge";
import { EmptyState } from "@/components/ui/states";
import { api } from "@/lib/api";
import { tr } from "@/lib/i18n/tr";

export const dynamic = "force-dynamic";

const MIN_QUERY_LENGTH = 2;

type Props = { searchParams: Promise<{ q?: string }> };

export const metadata: Metadata = { title: tr.search.title };

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-6">
      <h2 className="font-display text-primary mb-2 text-2xl font-semibold uppercase">
        {title}
      </h2>
      <ul className="bg-card divide-y rounded-lg border">{children}</ul>
    </section>
  );
}

const ROW = "hover:bg-muted/50 flex items-center gap-3 px-3 py-2.5";

export default async function SearchPage({ searchParams }: Props) {
  const q = ((await searchParams).q ?? "").trim();
  const tooShort = q.length < MIN_QUERY_LENGTH;
  const results = tooShort ? null : await api.search(q);
  const total = results
    ? results.competitions.length + results.teams.length + results.players.length
    : 0;

  return (
    <>
      <h1 className="font-display text-4xl font-bold tracking-tight uppercase">
        {tr.search.title}
      </h1>
      <div className="mt-4 max-w-xl">
        <SearchForm defaultValue={q} />
      </div>

      {tooShort ? (
        <EmptyState className="mt-6" title={q ? tr.search.tooShort : tr.search.prompt} />
      ) : total === 0 ? (
        <EmptyState className="mt-6" title={tr.search.empty(q)} />
      ) : (
        <>
          <p className="text-muted-foreground mt-4 text-sm">{tr.search.resultsFor(q)}</p>
          {results!.competitions.length > 0 && (
            <Section title={tr.search.competitions}>
              {results!.competitions.map((c) => (
                <li key={c.id}>
                  <Link href={competitionHref(c)} className={ROW}>
                    <TeamBadge team={{ name: c.name, logo_url: c.logo_url }} />
                    <span className="font-medium">{c.name}</span>
                    <span className="text-muted-foreground text-sm">{c.country}</span>
                  </Link>
                </li>
              ))}
            </Section>
          )}
          {results!.teams.length > 0 && (
            <Section title={tr.search.teams}>
              {results!.teams.map((team) => (
                <li key={team.id}>
                  <Link href={`/teams/${team.id}`} className={ROW}>
                    <TeamBadge team={team} />
                    <span className="font-medium">{team.name}</span>
                    <span className="text-muted-foreground text-sm">{team.country}</span>
                  </Link>
                </li>
              ))}
            </Section>
          )}
          {results!.players.length > 0 && (
            <Section title={tr.search.players}>
              {results!.players.map((p) => (
                <li key={p.id}>
                  <Link href={`/players/${p.id}`} className={ROW}>
                    <span className="font-medium">{p.name}</span>
                    <span className="text-muted-foreground text-sm">
                      {[p.position, p.team?.name].filter(Boolean).join(" · ")}
                    </span>
                  </Link>
                </li>
              ))}
            </Section>
          )}
        </>
      )}
    </>
  );
}
