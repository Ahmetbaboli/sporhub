"use client";

import { Star } from "lucide-react";
import { useRouter } from "next/navigation";
import { useOptimistic, useState, useTransition } from "react";
import { setFavorite } from "@/app/actions/account";
import { useT } from "@/lib/i18n/client";
import type { FavoriteKind } from "@/lib/types";
import { cn } from "@/lib/utils";

/** Star toggle with an optimistic state; rolls back and shows a message if saving fails. */
export function FavoriteButton({
  kind,
  id,
  name,
  initial,
}: {
  kind: FavoriteKind;
  id: number;
  name: string;
  initial: boolean;
}) {
  const tr = useT();
  const router = useRouter();
  const [saved, setSaved] = useState(initial);
  const [shown, setShown] = useOptimistic(saved);
  const [error, setError] = useState(false);
  const [pending, startTransition] = useTransition();

  function toggle() {
    const next = !shown;
    setError(false);
    startTransition(async () => {
      setShown(next);
      const result = await setFavorite(kind, id, next);
      if (result.ok) {
        setSaved(next);
      } else if (result.reason === "signed_out") {
        router.push(`/signin?callbackUrl=${encodeURIComponent(location.pathname)}`);
      } else {
        setError(true);
      }
    });
  }

  return (
    <span className="inline-flex flex-col items-start gap-1">
      <button
        type="button"
        onClick={toggle}
        disabled={pending}
        aria-pressed={shown}
        aria-label={shown ? tr.account.unfollowLabel(name) : tr.account.followLabel(name)}
        className={cn(
          "inline-flex h-9 items-center gap-1.5 rounded-md border px-3 text-sm font-medium transition-colors",
          shown
            ? "border-primary bg-primary text-primary-foreground"
            : "hover:bg-muted bg-card",
        )}
      >
        <Star className={cn("size-4", shown && "fill-current")} aria-hidden />
        {shown ? tr.account.following : tr.account.follow}
      </button>
      {error ? (
        <span role="status" className="text-accent text-xs">
          {tr.account.favoriteError}
        </span>
      ) : null}
    </span>
  );
}
