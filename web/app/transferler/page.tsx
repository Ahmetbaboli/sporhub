import type { Metadata } from "next";
import Link from "next/link";
import { NewsFeed } from "@/components/news/news-parts";
import { Reveal, SplitWords } from "@/components/motion/motion";
import { TeamBadge } from "@/components/sport/team-badge";
import { EmptyState } from "@/components/ui/states";
import { api } from "@/lib/api";
import { initLocale, t } from "@/lib/i18n";
import type { NewsItem, NewsTag } from "@/lib/types";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

const PER_COLUMN = 12;
const POOL = 50;
const HOT_TEAMS = 10;

type Props = { searchParams: Promise<{ team?: string }> };

export async function generateMetadata(): Promise<Metadata> {
  await initLocale();
  return { title: t().transfers.title };
}

/** Teams tagged most often across the latest transfer stories (real counts). */
function hotTeams(items: NewsItem[]): { tag: NewsTag; count: number }[] {
  const counts = new Map<number, { tag: NewsTag; count: number }>();
  for (const item of items) {
    for (const tag of item.tags.filter((x) => x.kind === "team")) {
      const entry = counts.get(tag.id) ?? { tag, count: 0 };
      entry.count += 1;
      counts.set(tag.id, entry);
    }
  }
  return [...counts.values()].sort((a, b) => b.count - a.count).slice(0, HOT_TEAMS);
}

function Column({
  title,
  items,
  tone,
}: {
  title: string;
  items: NewsItem[];
  tone: "official" | "rumour";
}) {
  return (
    <Reveal>
      <section aria-label={title}>
        <h2 className="mb-3 flex items-center gap-2 text-lg font-bold">
          <span
            aria-hidden
            className={cn(
              "size-2.5 rounded-full",
              tone === "official" ? "bg-accent" : "border-accent border-2 border-dashed",
            )}
          />
          {title}
          <span className="text-muted-foreground num text-sm font-medium">
            {t().transfers.mentions(items.length)}
          </span>
        </h2>
        {items.length ? (
          <NewsFeed items={items.slice(0, PER_COLUMN)} />
        ) : (
          <EmptyState title={t().transfers.empty} />
        )}
      </section>
    </Reveal>
  );
}

export default async function TransfersPage({ searchParams }: Props) {
  await initLocale();
  const { team: teamParam } = await searchParams;
  const team = teamParam && /^\d+$/.test(teamParam) ? Number(teamParam) : undefined;
  const [official, rumours] = await Promise.all([
    api.news({ category: "transfer_official", team, pageSize: POOL }).catch(() => null),
    api.news({ category: "transfer_rumour", team, pageSize: POOL }).catch(() => null),
  ]);
  const officialItems = official?.items ?? [];
  const rumourItems = rumours?.items ?? [];
  // Hot teams are counted over the unfiltered pool so the chips stay put while filtering.
  const pool = team
    ? await Promise.all([
        api.news({ category: "transfer_official", pageSize: POOL }).catch(() => null),
        api.news({ category: "transfer_rumour", pageSize: POOL }).catch(() => null),
      ]).then((pages) => pages.flatMap((p) => p?.items ?? []))
    : [...officialItems, ...rumourItems];
  const hot = hotTeams(pool);

  return (
    <>
      <span className="eyebrow mb-3">{t().news.categories.transfer}</span>
      <h1 className="font-display text-4xl leading-none font-bold tracking-tight uppercase sm:text-5xl">
        <SplitWords text={t().transfers.title} />
      </h1>
      <p className="text-muted-foreground mt-1.5 mb-5 text-sm">
        {t().transfers.subtitle}
      </p>

      {hot.length > 0 ? (
        <nav aria-label={t().transfers.hotTeams} className="mb-6">
          <p className="text-muted-foreground mb-2 text-xs font-bold tracking-[0.12em] uppercase">
            {t().transfers.hotTeams}
          </p>
          <ul className="scroll-strip flex gap-2 overflow-x-auto pb-1">
            <li className="shrink-0">
              <Link
                href="/transferler"
                aria-current={!team ? "page" : undefined}
                className={cn(
                  "inline-flex h-10 items-center rounded-full border px-4 text-sm font-semibold transition-colors duration-150",
                  !team
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-card hover:bg-muted",
                )}
              >
                {t().transfers.all}
              </Link>
            </li>
            {hot.map(({ tag, count }) => (
              <li key={tag.id} className="shrink-0">
                <Link
                  href={`/transferler?team=${tag.id}`}
                  aria-current={team === tag.id ? "page" : undefined}
                  className={cn(
                    "inline-flex h-10 items-center gap-2 rounded-full border pr-3 pl-1.5 text-sm font-medium transition-colors duration-150",
                    team === tag.id
                      ? "border-primary bg-primary/15"
                      : "bg-card hover:bg-muted",
                  )}
                >
                  <TeamBadge
                    team={{ name: tag.name, logo_url: tag.logo_url ?? null }}
                    size="sm"
                  />
                  {tag.name}
                  <span className="bg-muted num rounded px-1 text-xs">{count}</span>
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      ) : null}

      <div className="grid gap-8 lg:grid-cols-2">
        <Column title={t().transfers.official} items={officialItems} tone="official" />
        <Column title={t().transfers.rumours} items={rumourItems} tone="rumour" />
      </div>
    </>
  );
}
