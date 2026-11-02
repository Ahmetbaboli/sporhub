import { AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { formatRelative } from "@/lib/format";
import { intlLocale, t } from "@/lib/i18n";
import { PROVIDERS, providerName } from "@/lib/sources";

/**
 * "Source · last updated" line for a page, with a "data delayed" warning when the provider is
 * failing or late. `sport` limits it to that sport's providers; omitted = every configured one.
 */
export async function Freshness({ sport }: { sport?: string | null }) {
  const meta = await api.meta().catch(() => null);
  if (!meta) return null;
  const sources = meta.sources.filter(
    (s) => s.configured && s.sport && (!sport || s.sport === sport),
  );
  if (sources.length === 0) return null;
  const now = new Date();
  const anyStale = sources.some((s) => s.stale);
  return (
    <aside
      aria-label={t().freshness.label}
      className="text-muted-foreground mt-10 space-y-1 border-t pt-3 text-xs"
    >
      {anyStale ? (
        <p role="status" className="text-accent flex items-center gap-1.5 font-semibold">
          <AlertTriangle className="size-3.5" aria-hidden />
          {t().freshness.delayed} — {t().freshness.delayedBody}
        </p>
      ) : null}
      <ul className="flex flex-wrap gap-x-4 gap-y-1">
        {sources.map((s) => (
          <li key={s.name}>
            {t().freshness.source}:{" "}
            <a
              href={PROVIDERS[s.name]?.url ?? "#"}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline"
            >
              {providerName(s.name)}
            </a>{" "}
            ·{" "}
            {t().freshness.updated(
              s.last_success_at
                ? formatRelative(s.last_success_at, now, intlLocale())
                : t().freshness.never,
            )}
          </li>
        ))}
      </ul>
    </aside>
  );
}
