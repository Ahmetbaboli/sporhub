import Link from "next/link";
import { TeamBadge } from "@/components/sport/team-badge";
import {
  type CompareMetric,
  type CompareType,
  formatMetric,
  winner,
} from "@/lib/compare";
import { tr } from "@/lib/i18n/tr";
import type { Team } from "@/lib/types";
import { cn } from "@/lib/utils";

const PERCENT = 100;

export interface CompareSelection {
  type: CompareType;
  a?: number;
  b?: number;
  q?: string;
}

export function compareHref({ type, a, b, q }: CompareSelection): string {
  const params = new URLSearchParams({ type });
  if (a) params.set("a", String(a));
  if (b) params.set("b", String(b));
  if (q) params.set("q", q);
  return `/compare?${params.toString()}`;
}

export function TypeSwitch({ active }: { active: CompareType }) {
  const types: CompareType[] = ["teams", "players"];
  return (
    <nav aria-label={tr.compare.typeLabel} className="mb-6 flex gap-1">
      {types.map((type) => (
        <Link
          key={type}
          href={compareHref({ type })}
          aria-current={type === active ? "page" : undefined}
          className={cn(
            "rounded-md border px-3 py-1.5 text-sm font-medium",
            type === active
              ? "border-primary bg-primary text-primary-foreground"
              : "bg-card hover:bg-muted",
          )}
        >
          {tr.compare[type]}
        </Link>
      ))}
    </nav>
  );
}

export interface Pickable {
  id: number;
  name: string;
  team: Pick<Team, "name" | "logo_url"> | null;
  detail: string | null;
}

export function PickList({
  title,
  items,
  hrefFor,
}: {
  title: string;
  items: Pickable[];
  hrefFor: (id: number) => string;
}) {
  return (
    <section className="bg-card mt-4 overflow-hidden rounded-lg border">
      <h3 className="bg-muted/60 border-b px-3 py-2 text-sm font-semibold">{title}</h3>
      {items.length ? (
        <ul className="divide-y">
          {items.map((item) => (
            <li key={item.id}>
              <Link
                href={hrefFor(item.id)}
                className="hover:bg-muted/50 flex items-center gap-2 px-3 py-2 text-sm"
              >
                {item.team ? <TeamBadge team={item.team} size="sm" /> : null}
                <span className="font-medium">{item.name}</span>
                {item.detail ? (
                  <span className="text-muted-foreground ml-auto text-xs">
                    {item.detail}
                  </span>
                ) : null}
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-muted-foreground px-3 py-4 text-sm">{tr.compare.noResults}</p>
      )}
    </section>
  );
}

export function SearchBox({ selection }: { selection: CompareSelection }) {
  return (
    <form action="/compare" className="flex gap-2">
      <input type="hidden" name="type" value={selection.type} />
      {selection.a ? <input type="hidden" name="a" value={selection.a} /> : null}
      <label htmlFor="compare-q" className="sr-only">
        {tr.compare.searchLabel}
      </label>
      <input
        id="compare-q"
        name="q"
        type="search"
        minLength={2}
        defaultValue={selection.q}
        placeholder={tr.compare.searchPlaceholder[selection.type]}
        className="bg-card h-10 flex-1 rounded-md border px-3 text-sm"
      />
      <button
        type="submit"
        className="bg-primary text-primary-foreground h-10 rounded-md px-4 text-sm font-semibold"
      >
        {tr.compare.searchLabel}
      </button>
    </form>
  );
}

export interface Side {
  id: number;
  name: string;
  href: string;
  badge: Pick<Team, "name" | "logo_url"> | null;
  subtitle: string | null;
}

/** The two contenders, each with a link that clears that side. */
export function Contenders({
  a,
  b,
  selection,
}: {
  a: Side;
  b: Side;
  selection: CompareSelection;
}) {
  const card = (side: Side, clear: CompareSelection, align: "left" | "right") => (
    <div
      className={cn(
        "flex min-w-0 flex-1 flex-col gap-2",
        align === "right" ? "items-end text-right" : "items-start",
      )}
    >
      {side.badge ? <TeamBadge team={side.badge} size="lg" /> : null}
      <Link
        href={side.href}
        className="font-display text-2xl leading-none font-bold uppercase hover:underline sm:text-3xl"
      >
        {side.name}
      </Link>
      {side.subtitle ? (
        <span className="text-muted-foreground text-sm">{side.subtitle}</span>
      ) : null}
      <Link
        href={compareHref(clear)}
        className="text-primary text-xs font-medium underline"
      >
        {tr.compare.change}
      </Link>
    </div>
  );
  return (
    <div className="bg-card flex items-start gap-4 rounded-lg border p-4">
      {card(a, { type: selection.type, a: b.id }, "left")}
      <Link
        href={compareHref({ type: selection.type, a: b.id, b: a.id })}
        className="text-muted-foreground hover:bg-muted mt-6 shrink-0 rounded-md border px-2 py-1 text-xs"
      >
        {tr.compare.swap}
      </Link>
      {card(b, { type: selection.type, a: a.id }, "right")}
    </div>
  );
}

/** Mirrored bars: each side's share of the pair, the better side highlighted. */
function MetricRow({ metric }: { metric: CompareMetric }) {
  const best = winner(metric);
  const a = Math.abs(metric.a ?? 0);
  const b = Math.abs(metric.b ?? 0);
  const total = a + b;
  const share = (v: number) => (total ? Math.round((v / total) * PERCENT) : 0);
  const value = (side: "a" | "b") => (
    <span
      className={cn(
        "num w-16 shrink-0 text-base",
        side === "b" && "text-right",
        best === side ? "text-primary font-bold" : "text-muted-foreground",
      )}
    >
      {formatMetric(metric, side === "a" ? metric.a : metric.b)}
    </span>
  );
  return (
    <li className="px-3 py-2">
      <p className="text-muted-foreground mb-1 text-center text-xs font-semibold uppercase">
        {metric.label}
      </p>
      <div className="flex items-center gap-2">
        {value("a")}
        <span className="bg-muted flex h-2 flex-1 justify-end overflow-hidden rounded-l-full">
          <span
            className={cn(best === "a" ? "bg-primary" : "bg-muted-foreground/40")}
            style={{ width: `${share(a)}%` }}
          />
        </span>
        <span className="bg-muted flex h-2 flex-1 overflow-hidden rounded-r-full">
          <span
            className={cn(best === "b" ? "bg-primary" : "bg-muted-foreground/40")}
            style={{ width: `${share(b)}%` }}
          />
        </span>
        {value("b")}
      </div>
    </li>
  );
}

export function MetricList({ metrics }: { metrics: CompareMetric[] }) {
  if (metrics.length === 0) {
    return <p className="text-muted-foreground mt-4 text-sm">{tr.compare.noStats}</p>;
  }
  return (
    <ul className="bg-card mt-4 divide-y rounded-lg border">
      {metrics.map((m) => (
        <MetricRow key={m.key} metric={m} />
      ))}
    </ul>
  );
}
