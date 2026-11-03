import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { NewsFeed, NewsHero } from "@/components/news/news-parts";
import { NewsFeedSkeleton } from "@/components/sport/skeletons";
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
const HERO_SIZE = 3;
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

/** The unfiltered first page opens with a lead story; any filter shows a plain feed. */
function isFrontPage(state: NewsState): boolean {
  return (
    state.page === 1 &&
    state.tab === "all" &&
    !state.q &&
    !state.month &&
    !state.team &&
    !state.player &&
    !state.competition
  );
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
      <h1 className="font-display text-4xl leading-none font-bold tracking-tight uppercase sm:text-5xl">
        {t().news.title}
      </h1>
      <p className="text-muted-foreground mt-1.5 mb-5 text-sm">{t().news.subtitle}</p>
      <TabNav tabs={tabs} active={state.tab} label={t().news.filters} />
      <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <SportChips state={state} />
        <div className="flex flex-col gap-2 sm:flex-row">
          <SearchBox state={state} />
          <Suspense fallback={null}>
            <MonthFilter state={state} />
          </Suspense>
        </div>
      </div>
      <Suspense key={newsHref(state)} fallback={<NewsFeedSkeleton />}>
        <Results state={state} />
      </Suspense>
    </>
  );
}

/** Keeps the other filters when one control submits on its own. */
function HiddenFilters({ state, omit }: { state: NewsState; omit: "q" | "month" }) {
  const keep: [string, string | undefined][] = [
    ["category", state.tab !== "all" ? state.tab : undefined],
    ["sport", state.sport],
    ["q", omit === "q" ? undefined : state.q],
    ["month", omit === "month" ? undefined : state.month],
  ];
  return (
    <>
      {keep.map(([name, value]) =>
        value ? <input key={name} type="hidden" name={name} value={value} /> : null,
      )}
    </>
  );
}

function SearchBox({ state }: { state: NewsState }) {
  return (
    <form action="/news" className="flex gap-2">
      <HiddenFilters state={state} omit="q" />
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
        className="bg-card h-10 w-full min-w-0 rounded-md border px-3 text-sm sm:w-56"
      />
      <button
        type="submit"
        className="bg-primary text-primary-foreground h-10 rounded-md px-4 text-sm font-semibold"
      >
        {t().nav.search}
      </button>
    </form>
  );
}

function SportChips({ state }: { state: NewsState }) {
  const chip = (active: boolean) =>
    cn(
      "inline-flex h-8 items-center rounded-full border px-3 text-sm whitespace-nowrap transition-colors duration-150",
      active
        ? "border-primary bg-primary text-primary-foreground font-semibold"
        : "bg-card hover:bg-muted",
    );
  return (
    <ul className="scroll-strip flex gap-2 overflow-x-auto">
      <li className="shrink-0">
        <Link
          href={newsHref(state, { sport: undefined })}
          className={chip(!state.sport)}
          aria-current={!state.sport ? "page" : undefined}
        >
          {t().news.allSports}
        </Link>
      </li>
      {NEWS_SPORTS.map((sport) => (
        <li key={sport} className="shrink-0">
          <Link
            href={newsHref(state, { sport })}
            className={chip(state.sport === sport)}
            aria-current={state.sport === sport ? "page" : undefined}
          >
            {sportLabel(sport)}
          </Link>
        </li>
      ))}
    </ul>
  );
}

/** The archive as one compact month picker (GET form, works without JavaScript). */
async function MonthFilter({ state }: { state: NewsState }) {
  const archive = await api.newsArchive(query(state)).catch(() => null);
  if (!archive || archive.months.length === 0) return null;
  return (
    <form action="/news" className="flex gap-2">
      <HiddenFilters state={state} omit="month" />
      <label htmlFor="news-month" className="sr-only">
        {t().news.archiveFilter}
      </label>
      <select
        id="news-month"
        name="month"
        defaultValue={state.month ?? ""}
        className="bg-card h-10 rounded-md border px-2 text-sm"
      >
        <option value="">
          {t().news.archive}: {t().news.allTime}
        </option>
        {archive.months.map(({ month, count }) => (
          <option key={month} value={month}>
            {formatMonth(month, intlLocale())} ({count})
          </option>
        ))}
      </select>
      <button
        type="submit"
        className="bg-muted hover:bg-primary hover:text-primary-foreground h-10 rounded-md px-3 text-sm font-semibold transition-colors duration-150"
      >
        {t().news.apply}
      </button>
    </form>
  );
}

async function NoNews({ state }: { state: NewsState }) {
  // Say plainly when the server has no feeds at all, instead of blaming the filters.
  const meta = isFrontPage(state) ? await api.meta().catch(() => null) : null;
  if (meta && meta.news_feeds.length === 0) {
    return <EmptyState title={t().news.noFeeds} body={t().news.noFeedsBody} />;
  }
  return <EmptyState title={t().news.empty} />;
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
  if (page.items.length === 0) return <NoNews state={state} />;
  const hero = isFrontPage(state) && page.items.length >= HERO_SIZE;
  const feed = hero ? page.items.slice(HERO_SIZE) : page.items;
  return (
    <div className="space-y-6">
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
      {hero ? <NewsHero items={page.items.slice(0, HERO_SIZE)} /> : null}
      {feed.length > 0 ? (
        <section aria-labelledby="news-feed">
          <h2 id="news-feed" className={cn("mb-3 text-lg font-bold", !hero && "sr-only")}>
            {t().news.feed}
          </h2>
          <NewsFeed items={feed} />
        </section>
      ) : null}
      <Pagination
        page={state.page}
        pageSize={PAGE_SIZE}
        total={page.total}
        hrefFor={(p) => newsHref(state, { page: p })}
      />
    </div>
  );
}
