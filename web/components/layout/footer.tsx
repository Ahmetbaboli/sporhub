import Link from "next/link";
import { api } from "@/lib/api";
import { t } from "@/lib/i18n";
import { PROVIDERS } from "@/lib/sources";

/**
 * Attribution for the data providers in use, as each one asks for it (docs/DATA-SOURCES.md).
 * Providers that are not configured supply nothing, so they are not credited; if the API is
 * unreachable every provider is listed rather than none.
 */
export async function Footer() {
  const f = t().footer;
  const meta = await api.meta().catch(() => null);
  const active = new Set(meta?.sources.filter((s) => s.configured).map((s) => s.name));
  const providers = Object.entries(PROVIDERS).filter(([key]) => !meta || active.has(key));
  return (
    <footer className="text-muted-foreground border-t text-sm">
      <div className="mx-auto flex max-w-5xl flex-col gap-2 px-4 py-6 sm:flex-row sm:justify-between">
        <p>
          <span className="font-display text-foreground text-base font-semibold uppercase">
            {t().app.name}
          </span>{" "}
          — {t().app.tagline}
        </p>
        <nav aria-label={f.sources} className="flex gap-4">
          <Link href="/sources" className="hover:underline">
            {f.sources}
          </Link>
          <Link href="/about" className="hover:underline">
            {f.about}
          </Link>
          <Link href="/privacy" className="hover:underline">
            {f.privacy}
          </Link>
        </nav>
      </div>
      <div className="mx-auto max-w-5xl space-y-1 px-4 pb-6 text-xs">
        <p>{f.note}</p>
        <p>
          {providers.map(([key, p], i) => (
            <span key={key}>
              {i > 0 ? " · " : null}
              <a
                href={p.url}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:underline"
              >
                {p.attribution}
              </a>
              {p.licence ? (
                <>
                  {" "}
                  (
                  <a
                    href={p.licence.url}
                    target="_blank"
                    rel="noopener noreferrer license"
                    className="hover:underline"
                  >
                    {p.licence.name}
                  </a>
                  )
                </>
              ) : null}
            </span>
          ))}
          {" · "}
          {f.newsRights} {f.openSource}
        </p>
      </div>
    </footer>
  );
}
