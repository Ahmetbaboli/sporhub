import { ExternalLink, Zap } from "lucide-react";
import Link from "next/link";
import { formatRelative } from "@/lib/format";
import { intlLocale, t } from "@/lib/i18n";
import type { NewsCategory, NewsItem, NewsTag } from "@/lib/types";
import { cn } from "@/lib/utils";

const CATEGORY_STYLES: Record<NewsCategory, string> = {
  general: "bg-muted text-muted-foreground",
  transfer_official: "bg-primary text-primary-foreground",
  transfer_rumour: "border border-dashed border-primary text-primary",
  interview: "bg-muted text-foreground",
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
    <span className="bg-accent text-accent-foreground inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-bold tracking-wide uppercase">
      <Zap className="size-3" aria-hidden />
      {t().news.breaking}
    </span>
  );
}

function Meta({ item }: { item: NewsItem }) {
  return (
    <p className="text-muted-foreground flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
      {item.is_breaking ? <BreakingBadge /> : null}
      <CategoryBadge category={item.category} />
      <span>{item.source}</span>
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
            className="bg-card hover:bg-muted rounded-full border px-2 py-0.5 text-xs"
          >
            {tag.name}
          </Link>
        </li>
      ))}
    </ul>
  );
}

/** One headline in a list; the title opens our detail page, which links to the source. */
export function NewsCard({
  item,
  compact = false,
}: {
  item: NewsItem;
  compact?: boolean;
}) {
  return (
    <article className="space-y-1.5 px-3 py-3">
      <Meta item={item} />
      <h3 className={cn("leading-snug font-semibold", compact ? "text-sm" : "text-base")}>
        <Link href={`/news/${item.id}`} className="hover:underline">
          {item.title}
        </Link>
      </h3>
      {!compact && item.summary ? (
        <p className="text-muted-foreground text-sm">{item.summary}</p>
      ) : null}
      {!compact ? <TagChips tags={item.tags} /> : null}
    </article>
  );
}

export function NewsList({ items, compact }: { items: NewsItem[]; compact?: boolean }) {
  return (
    <ul className="bg-card divide-y rounded-lg border">
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
        <h2 className="font-display text-primary text-2xl font-semibold uppercase">
          {title}
        </h2>
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
      className="border-accent bg-card mb-6 flex flex-col gap-1 rounded-lg border-l-4 px-3 py-2 sm:flex-row sm:items-center sm:gap-3"
    >
      <BreakingBadge />
      <ul className="min-w-0 flex-1 space-y-1">
        {items.map((item) => (
          <li key={item.id} className="truncate text-sm font-medium">
            <Link href={`/news/${item.id}`} className="hover:underline">
              {item.title}
            </Link>
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
