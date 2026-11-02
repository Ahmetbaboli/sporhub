import Link from "next/link";
import { t } from "@/lib/i18n";
import { PROVIDERS } from "@/lib/sources";

/** Attribution for every data provider, as each one asks for it (docs/DATA-SOURCES.md). */
export function Footer() {
  const f = t().footer;
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
          {Object.entries(PROVIDERS).map(([key, p], i) => (
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
