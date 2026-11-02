import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { NewsList } from "@/components/news/news-parts";
import { EventCardsSkeleton } from "@/components/sport/skeletons";
import { Pagination } from "@/components/ui/pagination";
import { EmptyState } from "@/components/ui/states";
import { TabNav } from "@/components/ui/tab-nav";
import { api, type NewsQuery } from "@/lib/api";
import { sportLabel } from "@/lib/events";
import { formatMonth } from "@/lib/format";
import { initLocale, intlLocale, t } from "@/lib/i18n";
import {
  apiCategory,
  BREAKING_TAB,
  NEWS_TABS,
  newsHref,
  type NewsState,
  parseNewsState,
} from "@/lib/news-filters";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

const PAGE_SIZE = 15;
const NEWS_SPORTS = ["football", "basketball", "formula-1"] as const;

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };

export async function generateMetadata(): Promise<Metadata> {
  await initLocale();
  return { title: t().news.title };
}

function query(state: NewsState): Omit<NewsQuery, "page" | "pageSize"> {
  return {
    category: apiCategory(state.tab),
    breaking: state.tab === BREAKING_TAB ? true : undefined,
    sport: state.sport,
    q: state.q,
    team: state.team,
    player: state.player,
    competition: state.competition,
  };
}

export default async function NewsPage({ searchParams }: Props) {
  await initLocale();
  const state = parseNewsState(await searchParams);
  const labels = t().news.categories;
  const tabs = [
    ...NEWS_TABS.map((id) => ({
      id,
      label: labels[id],
      href: newsHref(state, { tab: id }),
    })),
    {
      id: BREAKING_TAB,
      label: t().news.breaking,
      href: newsHref(state, { tab: BREAKING_TAB }),
    },
  ];

  return (
    <>
      <h1 className="font-display text-4xl font-bold tracking-tight uppercase">
        {t().news.title}
      </h1>
      <p className="text-muted-foreground mt-1 mb-6 text-sm">{t().news.subtitle}</p>
      <TabNav tabs={tabs} active={state.tab} label={t().news.filters} />
      <div className="grid gap-6 lg:grid-cols-[1fr_15rem]">
        <div className="min-w-0 space-y-4">
          <SearchAndSports state={state} />
          <Suspense key={newsHref(state)} fallback={<EventCardsSkeleton cards={2} />}>
            <Results state={state} />
          </Suspense>
        </div>
        <Suspense fallback={null}>
          <Archive state={state} />
        </Suspense>
      </div>
    </>
  );
}

function SearchAndSports({ state }: { state: NewsState }) {
  const chip = (active: boolean) =>
    cn(
      "rounded-full border px-3 py-1 text-sm",
      active
        ? "border-primary bg-primary text-primary-foreground"
        : "bg-card hover:bg-muted",
    );
  return (
    <div className="space-y-3">
      <form action="/news" className="flex gap-2">
        {state.tab !== "all" ? (
          <input type="hidden" name="category" value={state.tab} />
        ) : null}
        {state.sport ? <input type="hidden" name="sport" value={state.sport} /> : null}
        <label htmlFor="news-q" className="sr-only">
          {t().nav.search}
        </label>
        <input
          id="news-q"
          name="q"
          type="search"
          minLength={2}
          defaultValue={state.q}
          placeholder={t().news.searchPlaceholder}
          className="bg-card h-10 flex-1 rounded-md border px-3 text-sm"
        />
        <button
          type="submit"
          className="bg-primary text-primary-foreground h-10 rounded-md px-4 text-sm font-semibold"
        >
          {t().nav.search}
        </button>
      </form>
      <ul className="flex flex-wrap gap-2">
        <li>
          <Link
            href={newsHref(state, { sport: undefined })}
            className={chip(!state.sport)}
          >
            {t().news.allSports}
          </Link>
        </li>
        {NEWS_SPORTS.map((sport) => (
          <li key={sport}>
            <Link
              href={newsHref(state, { sport })}
              className={chip(state.sport === sport)}
            >
              {sportLabel(sport)}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

async function Results({ state }: { state: NewsState }) {
  const page = await api.news({
    ...query(state),
    month: state.month,
    page: state.page,
    pageSize: PAGE_SIZE,
  });
  const about = page.items[0]?.tags.find(
    (tag) =>
      (tag.kind === "team" && tag.id === state.team) ||
      (tag.kind === "player" && tag.id === state.player) ||
      (tag.kind === "competition" && tag.id === state.competition),
  );
  return (
    <>
      {about ? (
        <p className="text-sm">
          <span className="font-semibold">{t().news.newsAbout(about.name)}</span>{" "}
          <Link
            href={newsHref(state, {
              team: undefined,
              player: undefined,
              competition: undefined,
            })}
            className="text-primary underline"
          >
            {t().news.categories.all}
          </Link>
        </p>
      ) : null}
      {page.items.length === 0 ? (
        <EmptyState title={t().news.empty} />
      ) : (
        <>
          <NewsList items={page.items} />
          <Pagination
            page={state.page}
            pageSize={PAGE_SIZE}
            total={page.total}
            hrefFor={(p) => newsHref(state, { page: p })}
          />
        </>
      )}
    </>
  );
}

async function Archive({ state }: { state: NewsState }) {
  const archive = await api.newsArchive(query(state));
  if (archive.months.length === 0) return null;
  const item = (active: boolean) =>
    cn(
      "flex justify-between rounded-md px-2 py-1.5 text-sm",
      active ? "bg-muted font-semibold" : "hover:bg-muted",
    );
  return (
    <aside aria-labelledby="news-archive" className="lg:pt-0">
      <h2
        id="news-archive"
        className="font-display text-primary mb-2 text-xl font-semibold uppercase"
      >
        {t().news.archive}
      </h2>
      <ul className="bg-card rounded-lg border p-1">
        <li>
          <Link
            href={newsHref(state, { month: undefined })}
            className={item(!state.month)}
          >
            {t().news.allTime}
          </Link>
        </li>
        {archive.months.map(({ month, count }) => (
          <li key={month}>
            <Link
              href={newsHref(state, { month })}
              className={item(state.month === month)}
              aria-current={state.month === month ? "page" : undefined}
            >
              <span>{formatMonth(month, intlLocale())}</span>
              <span className="num text-muted-foreground">{count}</span>
            </Link>
          </li>
        ))}
      </ul>
    </aside>
  );
}
