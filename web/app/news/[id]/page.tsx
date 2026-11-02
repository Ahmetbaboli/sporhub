import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import {
  BreakingBadge,
  CategoryBadge,
  NewsList,
  SourceLink,
  TagChips,
} from "@/components/news/news-parts";
import { api } from "@/lib/api";
import { orNotFound, parseId } from "@/lib/api-helpers";
import { formatRelative } from "@/lib/format";
import { initLocale, intlLocale, t } from "@/lib/i18n";
import type { NewsItem } from "@/lib/types";

export const dynamic = "force-dynamic";

const RELATED_LIMIT = 5;

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  await initLocale();
  const { id } = await params;
  const item = await api.newsArticle(parseId(id)).catch(() => null);
  return { title: item?.title ?? t().news.title, description: item?.summary };
}

export default async function NewsArticlePage({ params }: Props) {
  await initLocale();
  const item = await orNotFound(api.newsArticle(parseId((await params).id)));
  return (
    <article className="mx-auto max-w-2xl">
      <p className="text-muted-foreground mb-3 flex flex-wrap items-center gap-2 text-xs">
        <Link href="/news" className="text-primary font-medium hover:underline">
          {t().news.title}
        </Link>
        <span aria-hidden>›</span>
        {item.is_breaking ? <BreakingBadge /> : null}
        <CategoryBadge category={item.category} />
      </p>
      <h1 className="font-display text-3xl leading-tight font-bold sm:text-4xl">
        {item.title}
      </h1>
      <p className="text-muted-foreground mt-2 text-sm">
        {t().news.source}: {item.source}
        {item.author ? ` · ${item.author}` : ""} ·{" "}
        <time dateTime={item.published_at}>
          {formatRelative(item.published_at, new Date(), intlLocale())}
        </time>
      </p>
      {item.summary ? (
        <p className="mt-6 text-lg leading-relaxed">{item.summary}</p>
      ) : null}
      <div className="mt-6">
        <SourceLink item={item} />
      </div>
      {item.tags.length ? (
        <div className="mt-8 space-y-2">
          <h2 className="text-muted-foreground text-xs font-semibold uppercase">
            {t().news.mentioned}
          </h2>
          <TagChips tags={item.tags} />
        </div>
      ) : null}
      <Suspense fallback={null}>
        <Related item={item} />
      </Suspense>
    </article>
  );
}

/** Other stories about the first tagged team/player/league, else the same category. */
async function Related({ item }: { item: NewsItem }) {
  const tag = item.tags[0];
  const page = await api.news({
    team: tag?.kind === "team" ? tag.id : undefined,
    player: tag?.kind === "player" ? tag.id : undefined,
    competition: tag?.kind === "competition" ? tag.id : undefined,
    category: tag ? undefined : item.category,
    pageSize: RELATED_LIMIT + 1,
  });
  const related = page.items.filter((n) => n.id !== item.id).slice(0, RELATED_LIMIT);
  if (related.length === 0) return null;
  return (
    <section className="mt-10" aria-labelledby="related-news">
      <h2
        id="related-news"
        className="font-display text-primary mb-3 text-2xl font-semibold uppercase"
      >
        {t().news.related}
      </h2>
      <NewsList items={related} compact />
    </section>
  );
}
