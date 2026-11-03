import { ExternalLink, Zap } from "lucide-react";
import Link from "next/link";
import { NewsCover } from "@/components/news/news-cover";
import { formatRelative } from "@/lib/format";
import { intlLocale, t } from "@/lib/i18n";
import type { NewsCategory, NewsItem, NewsTag } from "@/lib/types";
import { cn } from "@/lib/utils";

const CATEGORY_STYLES: Record<NewsCategory, string> = {
  general: "bg-muted text-muted-foreground",
  transfer_official: "bg-accent text-accent-foreground",
  transfer_rumour: "border border-dashed border-accent text-accent",
  interview: "bg-primary/15 text-primary",
  tournament: "bg-muted text-foreground",
};

export function tagHref(tag: NewsTag): string {
  if (tag.kind === "team") return `/teams/${tag.id}`;
  if (tag.kind === "player") return `/players/${tag.id}`;
  return `/${tag.sport_slug}/${tag.slug}`;
}

export function CategoryBadge({ category }: { category: NewsCategory }) {
  return (
    <span
      className={cn(
        "rounded px-1.5 py-0.5 text-[11px] font-semibold tracking-wide uppercase",
        CATEGORY_STYLES[category],
      )}
    >
      {t().news.categories[category]}
    </span>
  );
}

export function BreakingBadge() {
  return (
    <span className="bg-live text-live-foreground inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-bold tracking-wide uppercase">
      <Zap className="size-3" aria-hidden />
      {t().news.breaking}
    </span>
  );
}

/** Category, source and publish time: always visible, in that order. */
function Meta({ item, category = true }: { item: NewsItem; category?: boolean }) {
  return (
    <p className="text-muted-foreground flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
      {item.is_breaking ? <BreakingBadge /> : null}
      {category ? <CategoryBadge category={item.category} /> : null}
      <span className="text-foreground/90 font-semibold">{item.source}</span>
      <span aria-hidden>·</span>
      <time dateTime={item.published_at}>
        {formatRelative(item.published_at, new Date(), intlLocale())}
      </time>
    </p>
  );
}

export function TagChips({ tags }: { tags: NewsTag[] }) {
  if (tags.length === 0) return null;
  return (
    <ul className="flex flex-wrap gap-1.5" aria-label={t().news.mentioned}>
      {tags.map((tag) => (
        <li key={`${tag.kind}-${tag.id}`}>
          <Link
            href={tagHref(tag)}
            className="bg-card hover:bg-muted rounded-full border px-2 py-0.5 text-xs transition-colors duration-150"
          >
            {tag.name}
          </Link>
        </li>
      ))}
    </ul>
  );
}

/** The original article at the publisher (new tab); we only show headline + short summary. */
function ExternalNewsLink({
  item,
  children,
}: {
  item: NewsItem;
  children: React.ReactNode;
}) {
  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer nofollow"
      className="hover:underline"
    >
      {children}
      <span className="sr-only">
        {" "}
        — {item.source} ({t().news.externalNote})
      </span>
    </a>
  );
}

/** The cover is a second, mouse-only way into the same external article. */
function CoverLink({
  item,
  className,
  size,
}: {
  item: NewsItem;
  className?: string;
  size?: "sm" | "md" | "lg";
}) {
  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer nofollow"
      tabIndex={-1}
      aria-hidden
      className={cn("block shrink-0 overflow-hidden rounded-lg", className)}
    >
      <NewsCover
        sport={item.sport_slug}
        imageUrl={item.image_url}
        caption={item.source}
        size={size}
        className="size-full"
      />
    </a>
  );
}

/** Lead story plus two secondary ones (first page of the news feed). */
export function NewsHero({ items }: { items: NewsItem[] }) {
  const [lead, ...rest] = items;
  if (!lead) return null;
  return (
    <section
      aria-label={t().news.headline}
      className="grid gap-4 lg:grid-cols-[1.6fr_1fr]"
    >
      <article className="glass lift overflow-hidden rounded-xl">
        <CoverLink item={lead} size="lg" className="aspect-[16/7] rounded-none" />
        <div className="space-y-2 p-4">
          <Meta item={lead} />
          <h2 className="text-xl leading-snug font-bold sm:text-2xl">
            <ExternalNewsLink item={lead}>{lead.title}</ExternalNewsLink>
          </h2>
          {lead.summary ? (
            <p className="text-muted-foreground line-clamp-3 text-sm">{lead.summary}</p>
          ) : null}
          <TagChips tags={lead.tags} />
        </div>
      </article>
      <div className="grid content-start gap-4">
        {rest.slice(0, 2).map((item) => (
          <article
            key={item.id}
            className="bg-card lift flex gap-3 overflow-hidden rounded-xl border p-3"
          >
            <CoverLink item={item} size="md" className="aspect-[4/3] w-28 sm:w-40" />
            <div className="min-w-0 space-y-1.5">
              <Meta item={item} />
              <h3 className="line-clamp-3 leading-snug font-semibold">
                <ExternalNewsLink item={item}>{item.title}</ExternalNewsLink>
              </h3>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

/** Scannable feed: cover thumbnail, meta line, headline, summary, tags. */
export function NewsFeed({ items }: { items: NewsItem[] }) {
  return (
    <ul className="grid gap-3">
      {items.map((item) => (
        <li key={item.id}>
          <div className="bg-card hover:bg-muted/40 flex gap-3 rounded-xl border p-3 transition-colors duration-150 sm:gap-4">
            <CoverLink
              item={item}
              size="sm"
              className="aspect-[4/3] w-24 self-start sm:aspect-[16/10] sm:w-44"
            />
            <div className="min-w-0 flex-1">
              <NewsCard item={item} bare />
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}

/** Narrow column of latest headlines with small covers (home page side rail). */
export function NewsRail({
  title,
  items,
  moreHref,
}: {
  title: string;
  items: NewsItem[];
  moreHref: string;
}) {
  if (items.length === 0) return null;
  return (
    <section aria-labelledby="news-rail">
      <div className="mb-2 flex items-baseline justify-between gap-2">
        <h2 id="news-rail" className="text-lg font-bold">
          {title}
        </h2>
        <Link
          href={moreHref}
          className="text-primary text-sm font-medium hover:underline"
        >
          {t().news.seeAll}
        </Link>
      </div>
      <ul className="bg-card divide-y overflow-hidden rounded-xl border">
        {items.map((item, index) => (
          <li key={item.id} className="p-3">
            {index === 0 ? (
              <CoverLink item={item} size="md" className="mb-2.5 aspect-[16/8] w-full" />
            ) : null}
            <Meta item={item} category={false} />
            <h3 className="mt-1 text-sm leading-snug font-semibold">
              <ExternalNewsLink item={item}>{item.title}</ExternalNewsLink>
            </h3>
          </li>
        ))}
      </ul>
    </section>
  );
}

/** One headline in a list; the title opens the original article at the publisher. */
export function NewsCard({
  item,
  compact = false,
  bare = false,
}: {
  item: NewsItem;
  compact?: boolean;
  /** Inside another card (no padding of its own). */
  bare?: boolean;
}) {
  return (
    <article className={cn("space-y-1.5", !bare && "px-3 py-3")}>
      <Meta item={item} />
      <h3
        className={cn("leading-snug font-semibold", compact ? "text-sm" : "text-[15px]")}
      >
        <ExternalNewsLink item={item}>{item.title}</ExternalNewsLink>
      </h3>
      {!compact && item.summary ? (
        <p className="text-muted-foreground line-clamp-2 text-sm">{item.summary}</p>
      ) : null}
      {item.also_sources.length ? (
        <p className="text-muted-foreground text-xs">
          {t().news.alsoReported}{" "}
          {item.also_sources.map((other, i) => (
            <span key={other.url}>
              {i > 0 ? ", " : null}
              <a
                href={other.url}
                target="_blank"
                rel="noopener noreferrer nofollow"
                className="hover:underline"
              >
                {other.source}
              </a>
            </span>
          ))}
        </p>
      ) : null}
      {!compact ? <TagChips tags={item.tags} /> : null}
    </article>
  );
}

export function NewsList({ items, compact }: { items: NewsItem[]; compact?: boolean }) {
  return (
    <ul className="bg-card divide-y rounded-xl border">
      {items.map((item) => (
        <li key={item.id}>
          <NewsCard item={item} compact={compact} />
        </li>
      ))}
    </ul>
  );
}

/** A titled box of recent headlines with a link to the full, pre-filtered list. */
export function NewsBox({
  title,
  items,
  moreHref,
}: {
  title: string;
  items: NewsItem[];
  moreHref: string;
}) {
  if (items.length === 0) return null;
  return (
    <section className="mt-8" aria-label={title}>
      <div className="mb-3 flex items-baseline justify-between gap-2">
        <h2 className="text-lg font-bold">{title}</h2>
        <Link
          href={moreHref}
          className="text-primary text-sm font-medium hover:underline"
        >
          {t().news.seeAll}
        </Link>
      </div>
      <NewsList items={items} compact />
    </section>
  );
}

/** Thin strip of breaking headlines for the home page. */
export function BreakingStrip({ items }: { items: NewsItem[] }) {
  if (items.length === 0) return null;
  return (
    <section
      aria-label={t().news.breaking}
      className="border-l-live bg-card mb-6 flex flex-col gap-1 rounded-lg border border-l-4 px-3 py-2 sm:flex-row sm:items-center sm:gap-3"
    >
      <BreakingBadge />
      <ul className="min-w-0 flex-1 space-y-1">
        {items.map((item) => (
          <li key={item.id} className="truncate text-sm font-medium">
            <ExternalNewsLink item={item}>{item.title}</ExternalNewsLink>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function SourceLink({ item }: { item: NewsItem }) {
  return (
    <a
      href={item.url}
      target="_blank"
      rel="noopener noreferrer nofollow"
      className="bg-primary text-primary-foreground inline-flex h-10 items-center gap-2 rounded-md px-4 text-sm font-semibold"
    >
      {t().news.readAtSource(item.source)}
      <ExternalLink className="size-4" aria-hidden />
      <span className="sr-only">({t().news.externalNote})</span>
    </a>
  );
}
