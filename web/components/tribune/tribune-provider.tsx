"use client";

import { Star } from "lucide-react";
import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useState, useTransition } from "react";
import { useT } from "@/lib/i18n/client";
import {
  serializeTribune,
  toggleInTribune,
  TRIBUNE_COOKIE,
  TRIBUNE_MAX_AGE_SECONDS,
  type Tribune,
  type TribuneKind,
} from "@/lib/tribune";
import { cn } from "@/lib/utils";

interface TribuneContextValue {
  tribune: Tribune;
  toggle: (kind: TribuneKind, id: number) => void;
  replace: (next: Tribune) => void;
}

const TribuneContext = createContext<TribuneContextValue | null>(null);

function writeCookie(tribune: Tribune) {
  const value = encodeURIComponent(serializeTribune(tribune));
  document.cookie = `${TRIBUNE_COOKIE}=${value}; Path=/; Max-Age=${TRIBUNE_MAX_AGE_SECONDS}; SameSite=Lax`;
}

/** Holds the on-device favourites; the server reads the same cookie to order content. */
export function TribuneProvider({
  initial,
  children,
}: {
  initial: Tribune;
  children: React.ReactNode;
}) {
  const [tribune, setTribune] = useState(initial);
  const router = useRouter();
  const [, startTransition] = useTransition();

  const replace = useCallback(
    (next: Tribune) => {
      setTribune(next);
      writeCookie(next);
      // Server components re-read the cookie so prioritised sections update too.
      startTransition(() => router.refresh());
    },
    [router],
  );
  const toggle = useCallback(
    (kind: TribuneKind, id: number) => replace(toggleInTribune(tribune, kind, id)),
    [replace, tribune],
  );

  return (
    <TribuneContext.Provider value={{ tribune, toggle, replace }}>
      {children}
    </TribuneContext.Provider>
  );
}

/** null outside a provider (isolated component tests); the root layout always provides one. */
export function useTribune(): TribuneContextValue | null {
  return useContext(TribuneContext);
}

/**
 * Star toggle for one team, league, driver or match. `label` names the thing for screen
 * readers ("Galatasaray tribüne ekle"); `withText` shows the state next to the icon.
 */
export function TribuneStar({
  kind,
  id,
  name,
  withText = false,
  className,
}: {
  kind: TribuneKind;
  id: number;
  name: string;
  withText?: boolean;
  className?: string;
}) {
  const tr = useT();
  const store = useTribune();
  if (!store) return null;
  const active = store.tribune[kind].includes(id);
  const label =
    kind === "matches"
      ? active
        ? tr.tribune.unfollowMatch(name)
        : tr.tribune.followMatch(name)
      : active
        ? tr.tribune.remove(name)
        : tr.tribune.add(name);
  return (
    <button
      type="button"
      onClick={() => store.toggle(kind, id)}
      aria-pressed={active}
      aria-label={withText ? undefined : label}
      title={label}
      className={cn(
        "inline-flex shrink-0 items-center justify-center gap-1.5 rounded-md transition-colors duration-150",
        withText
          ? "bg-card hover:bg-muted h-9 border px-3 text-sm font-medium"
          : "hover:bg-muted size-9",
        active ? "text-accent" : "text-muted-foreground hover:text-foreground",
        className,
      )}
    >
      <Star className={cn("size-4", active && "fill-current")} aria-hidden />
      {withText ? (
        <>
          <span>{active ? tr.tribune.added : tr.tribune.addShort}</span>
          <span className="sr-only"> — {name}</span>
        </>
      ) : null}
    </button>
  );
}
