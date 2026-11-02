import type { Metadata } from "next";
import { api } from "@/lib/api";
import { sportLabel } from "@/lib/events";
import { initLocale, t } from "@/lib/i18n";
import { PROVIDERS, providerName } from "@/lib/sources";

export const dynamic = "force-dynamic";

const REPO_DOC = "https://github.com/Ahmetbaboli/sporhub/blob/main/docs/DATA-SOURCES.md";

export async function generateMetadata(): Promise<Metadata> {
  await initLocale();
  return { title: t().sources.title };
}

export default async function SourcesPage() {
  await initLocale();
  const s = t().sources;
  const meta = await api.meta().catch(() => null);
  const section = "font-display text-primary mt-8 mb-3 text-2xl font-semibold uppercase";
  return (
    <article className="mx-auto max-w-3xl">
      <h1 className="font-display text-4xl font-bold tracking-tight uppercase">
        {s.title}
      </h1>
      <p className="mt-3">{s.intro}</p>

      <h2 className={section}>{s.dataTitle}</h2>
      <ul className="bg-card divide-y rounded-lg border">
        {Object.entries(PROVIDERS).map(([key, p]) => {
          const source = meta?.sources.find((x) => x.name === key);
          return (
            <li key={key} className="space-y-1 px-4 py-3 text-sm">
              <p className="flex flex-wrap items-baseline gap-2">
                <a
                  href={p.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-semibold hover:underline"
                >
                  {providerName(key)}
                </a>
                {source?.sport ? (
                  <span className="text-muted-foreground text-xs">
                    {sportLabel(source.sport)}
                  </span>
                ) : null}
                <span
                  className={
                    source?.configured
                      ? "bg-primary text-primary-foreground rounded px-1.5 text-xs"
                      : "bg-muted text-muted-foreground rounded px-1.5 text-xs"
                  }
                >
                  {source?.configured ? s.configured : s.notConfigured}
                </span>
              </p>
              <p>{p.attribution}</p>
              {p.licence ? (
                <p className="text-muted-foreground text-xs">
                  {s.licence}:{" "}
                  <a
                    href={p.licence.url}
                    rel="license noopener noreferrer"
                    target="_blank"
                    className="underline"
                  >
                    {p.licence.name}
                  </a>
                </p>
              ) : null}
            </li>
          );
        })}
      </ul>

      <h2 className={section}>{s.newsTitle}</h2>
      <p className="mb-3 text-sm">{s.newsIntro}</p>
      {meta?.news_feeds.length ? (
        <ul className="bg-card divide-y rounded-lg border text-sm">
          {meta.news_feeds.map((feed) => (
            <li key={feed.url} className="flex flex-wrap items-baseline gap-2 px-4 py-2">
              <a
                href={feed.site}
                target="_blank"
                rel="noopener noreferrer"
                className="font-semibold hover:underline"
              >
                {feed.name}
              </a>
              <span className="text-muted-foreground text-xs">
                {feed.sport ? sportLabel(feed.sport) : "—"} ·{" "}
                {feed.language.toUpperCase()}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-muted-foreground text-sm">{s.newsNone}</p>
      )}

      <h2 className={section}>{s.imagesTitle}</h2>
      <p className="text-sm">{s.images}</p>
      <p className="text-muted-foreground mt-8 text-xs">
        {s.details}{" "}
        <a
          href={REPO_DOC}
          target="_blank"
          rel="noopener noreferrer"
          className="underline"
        >
          {s.detailsLink}
        </a>
      </p>
    </article>
  );
}
