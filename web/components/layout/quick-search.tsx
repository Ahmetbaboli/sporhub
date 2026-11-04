"use client";

import { ArrowRight, Loader2, Search, Trophy, User } from "lucide-react";
import { useRouter } from "next/navigation";
import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import { TeamBadge } from "@/components/sport/team-badge";
import { useT } from "@/lib/i18n/client";
import {
  fetchQuickResults,
  flattenResults,
  isOpenShortcut,
  MIN_QUICK_QUERY,
  type QuickItem,
  type QuickKind,
} from "@/lib/quick-search";
import { cn } from "@/lib/utils";

const DEBOUNCE_MS = 180;

type Status = "idle" | "loading" | "done" | "error";

/** Results of one query; a newer query shows the previous rows until its own arrive. */
interface Fetched {
  query: string;
  items: QuickItem[];
  failed: boolean;
}

const noSubscription = () => () => {};
const isMacPlatform = () =>
  /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);

/** Header button + Ctrl+K (⌘K, "/") dialog with instant results. */
export function QuickSearch() {
  const m = useT();
  const [open, setOpen] = useState(false);
  // Server render and first paint say "Ctrl"; Apple devices then show ⌘.
  const isMac = useSyncExternalStore(noSubscription, isMacPlatform, () => false);
  const opener = useRef<HTMLElement | null>(null);

  const show = useCallback(() => {
    opener.current = document.activeElement as HTMLElement | null;
    setOpen(true);
  }, []);
  const hide = useCallback(() => {
    setOpen(false);
    opener.current?.focus?.();
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!isOpenShortcut(e)) return;
      e.preventDefault();
      setOpen((wasOpen) => {
        if (!wasOpen) opener.current = document.activeElement as HTMLElement | null;
        return !wasOpen;
      });
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <>
      <button
        type="button"
        onClick={show}
        aria-label={m.quickSearch.open}
        aria-keyshortcuts={isMac ? "Meta+K" : "Control+K"}
        className="text-muted-foreground hover:text-foreground bg-muted/60 absolute top-1/2 right-2 hidden -translate-y-1/2 items-center gap-0.5 rounded border px-1.5 py-0.5 font-mono text-[11px] sm:inline-flex"
      >
        <kbd className="font-mono">{isMac ? "⌘" : "Ctrl"}</kbd>
        <kbd className="font-mono">K</kbd>
      </button>
      {open ? <QuickSearchDialog onClose={hide} /> : null}
    </>
  );
}

function QuickSearchDialog({ onClose }: { onClose: () => void }) {
  const m = useT();
  const router = useRouter();
  const listId = useId();
  const input = useRef<HTMLInputElement>(null);
  const [q, setQ] = useState("");
  const [fetched, setFetched] = useState<Fetched | null>(null);
  const [active, setActive] = useState(0);
  const query = q.trim();
  const short = query.length < MIN_QUICK_QUERY;
  const items = short ? [] : (fetched?.items ?? []);
  const status: Status = short
    ? "idle"
    : fetched?.query !== query
      ? "loading"
      : fetched.failed
        ? "error"
        : "done";

  useEffect(() => {
    input.current?.focus();
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = overflow;
    };
  }, []);

  useEffect(() => {
    if (query.length < MIN_QUICK_QUERY) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      fetchQuickResults(query, controller.signal)
        .then((results) => {
          setFetched({ query, items: flattenResults(results, query), failed: false });
          setActive(0);
        })
        .catch(() => {
          if (!controller.signal.aborted) setFetched({ query, items: [], failed: true });
        });
    }, DEBOUNCE_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  // Keep the highlighted row visible while moving with the arrow keys.
  useEffect(() => {
    document
      .getElementById(`${listId}-${active}`)
      ?.scrollIntoView?.({ block: "nearest" });
  }, [active, listId]);

  const go = (item: QuickItem | undefined) => {
    if (!item) return;
    onClose();
    router.push(item.href);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      e.preventDefault();
      onClose();
    } else if (e.key === "ArrowDown" && items.length) {
      e.preventDefault();
      setActive((i) => (i + 1) % items.length);
    } else if (e.key === "ArrowUp" && items.length) {
      e.preventDefault();
      setActive((i) => (i - 1 + items.length) % items.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      go(items[active]);
    } else if (e.key === "Tab") {
      e.preventDefault(); // focus stays in the dialog; arrows move through results
    }
  };

  const results = items.filter((i) => i.kind !== "all");
  const optionId = (i: number) => `${listId}-${i}`;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 px-4 pt-[12vh] backdrop-blur-sm"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={m.quickSearch.title}
        onKeyDown={onKeyDown}
        className="bg-card w-full max-w-xl overflow-hidden rounded-xl border shadow-2xl"
      >
        <div className="flex items-center gap-2 border-b px-3">
          {status === "loading" ? (
            <Loader2 aria-hidden className="text-muted-foreground size-4 animate-spin" />
          ) : (
            <Search aria-hidden className="text-muted-foreground size-4" />
          )}
          <input
            ref={input}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            role="combobox"
            aria-expanded={items.length > 0}
            aria-controls={listId}
            aria-autocomplete="list"
            aria-activedescendant={items.length ? optionId(active) : undefined}
            aria-label={m.quickSearch.title}
            placeholder={m.nav.searchPlaceholder}
            autoComplete="off"
            spellCheck={false}
            className="placeholder:text-muted-foreground h-12 flex-1 bg-transparent text-base outline-none"
          />
          <kbd className="text-muted-foreground rounded border px-1.5 py-0.5 font-mono text-[11px]">
            Esc
          </kbd>
        </div>

        <ul id={listId} role="listbox" className="max-h-[55vh] overflow-y-auto p-1.5">
          {items.map((item, i) => (
            <QuickRow
              key={item.key}
              id={optionId(i)}
              item={item}
              selected={i === active}
              heading={groupHeading(items, i, m)}
              onHover={() => setActive(i)}
              onPick={() => go(item)}
            />
          ))}
        </ul>

        <p
          aria-live="polite"
          className={cn(
            "text-muted-foreground px-4 text-sm",
            (status !== "done" || results.length === 0) && "pb-4",
          )}
        >
          {status === "idle"
            ? m.quickSearch.hint
            : status === "error"
              ? m.quickSearch.error
              : status === "done" && results.length === 0
                ? m.search.empty(query)
                : status === "done"
                  ? m.quickSearch.count(results.length)
                  : ""}
        </p>

        <div className="text-muted-foreground bg-muted/40 mt-2 hidden gap-4 border-t px-4 py-2 text-xs sm:flex">
          <span>
            <kbd className="font-mono">↑↓</kbd> {m.quickSearch.keyMove}
          </span>
          <span>
            <kbd className="font-mono">Enter</kbd> {m.quickSearch.keyOpen}
          </span>
          <span>
            <kbd className="font-mono">Esc</kbd> {m.quickSearch.keyClose}
          </span>
        </div>
      </div>
    </div>
  );
}

function groupHeading(
  items: QuickItem[],
  i: number,
  m: ReturnType<typeof useT>,
): string | null {
  const kind = items[i].kind;
  if (kind === "all" || (i > 0 && items[i - 1].kind === kind)) return null;
  const titles: Record<Exclude<QuickKind, "all">, string> = {
    competition: m.search.competitions,
    team: m.search.teams,
    player: m.search.players,
  };
  return titles[kind];
}

function QuickRow({
  id,
  item,
  selected,
  heading,
  onHover,
  onPick,
}: {
  id: string;
  item: QuickItem;
  selected: boolean;
  heading: string | null;
  onHover: () => void;
  onPick: () => void;
}) {
  const m = useT();
  return (
    <>
      {heading ? (
        <li
          role="presentation"
          className="text-muted-foreground px-2.5 pt-2 pb-1 text-[11px] font-semibold tracking-wide uppercase"
        >
          {heading}
        </li>
      ) : null}
      <li
        id={id}
        role="option"
        aria-selected={selected}
        onMouseMove={onHover}
        onClick={onPick}
        className={cn(
          "flex cursor-pointer items-center gap-3 rounded-md px-2.5 py-2 text-sm",
          selected ? "bg-primary/15 text-foreground" : "hover:bg-muted/50",
          item.kind === "all" && "mt-1 border-t",
        )}
      >
        <RowIcon item={item} />
        <span className="min-w-0 flex-1">
          <span className="block truncate font-medium">
            {item.kind === "all" ? m.quickSearch.seeAll(item.title) : item.title}
          </span>
          {item.subtitle ? (
            <span className="text-muted-foreground block truncate text-xs">
              {item.subtitle}
            </span>
          ) : null}
        </span>
        {selected ? <ArrowRight aria-hidden className="text-primary size-4" /> : null}
      </li>
    </>
  );
}

function RowIcon({ item }: { item: QuickItem }) {
  const box =
    "bg-muted text-muted-foreground inline-flex size-7 shrink-0 items-center justify-center rounded-lg";
  if (item.kind === "team")
    return (
      <TeamBadge
        team={{ name: item.title, logo_url: item.logo_url, short_name: item.short_name }}
        size="sm"
      />
    );
  if (item.kind === "competition")
    return item.logo_url ? (
      <TeamBadge
        team={{ name: item.title, logo_url: item.logo_url }}
        size="sm"
        variant="competition"
      />
    ) : (
      <span aria-hidden className={box}>
        <Trophy className="size-4" />
      </span>
    );
  if (item.kind === "player")
    return (
      <span aria-hidden className={box}>
        <User className="size-4" />
      </span>
    );
  return (
    <span aria-hidden className={box}>
      <Search className="size-4" />
    </span>
  );
}
