import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { EmptyState } from "@/components/ui/states";
import { api } from "@/lib/api";
import { formatRelative } from "@/lib/format";
import { initLocale, intlLocale, t } from "@/lib/i18n";
import { getViewer, isAdmin } from "@/lib/session";
import { providerName } from "@/lib/sources";
import type { AdminStatus } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata: Metadata = { robots: { index: false } };

const PERCENT = 100;

/** Admins only (ADMIN_ACCOUNT_IDS); everyone else gets a plain 404, not a hint it exists. */
export default async function AdminStatusPage() {
  await initLocale();
  const viewer = await getViewer().catch(() => null);
  if (!isAdmin(viewer)) notFound();
  const token = process.env.ADMIN_TOKEN ?? "";
  const status = token ? await api.admin.status(token).catch(() => null) : null;
  const m = t().admin;
  if (!status) return <EmptyState title={m.unavailable} />;
  return (
    <>
      <h1 className="font-display text-4xl font-bold tracking-tight uppercase">
        {m.statusTitle}
      </h1>
      <p className="text-muted-foreground mt-1 mb-6 text-sm">
        {m.mode}: <strong>{status.data_mode}</strong> · {m.scheduler}:{" "}
        <strong>{status.scheduler_enabled ? m.on : m.off}</strong>
      </p>
      <StatusTable status={status} />
    </>
  );
}

function StatusTable({ status }: { status: AdminStatus }) {
  const m = t().admin;
  const now = new Date();
  return (
    <div className="bg-card overflow-x-auto rounded-lg border">
      <table className="num w-full text-sm">
        <caption className="sr-only">{m.statusTitle}</caption>
        <thead className="text-muted-foreground bg-muted/60 text-left text-xs">
          <tr>
            {[
              m.source,
              m.configured,
              m.lastSuccess,
              m.lastStatus,
              m.errorRate,
              m.budget,
            ].map((h) => (
              <th key={h} scope="col" className="px-3 py-2">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y align-top">
          {status.sources.map((s) => (
            <tr key={s.name}>
              <th scope="row" className="px-3 py-2 text-left font-semibold">
                {providerName(s.name)}
                {s.last_error ? (
                  <p className="text-muted-foreground mt-1 max-w-xs text-xs font-normal break-words">
                    {m.lastError}: {s.last_error}
                  </p>
                ) : null}
              </th>
              <td className="px-3 py-2">{s.configured ? m.yes : m.no}</td>
              <td className="px-3 py-2">
                {s.last_success_at
                  ? formatRelative(s.last_success_at, now, intlLocale())
                  : "–"}
              </td>
              <td
                className={s.stale ? "text-accent px-3 py-2 font-semibold" : "px-3 py-2"}
              >
                {s.last_status ?? "–"}
              </td>
              <td className="px-3 py-2">
                %{Math.round(s.error_rate_24h * PERCENT)}
                <span className="text-muted-foreground block text-xs">
                  {m.runs(s.runs_24h, s.failures_24h)}
                </span>
              </td>
              <td className="px-3 py-2 text-xs">
                {Object.entries(s.budget).map(([window, b]) => (
                  <span key={window} className="block">
                    {window}: {b.remaining}/{b.limit}
                  </span>
                ))}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
