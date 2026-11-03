"use client";

import { Trash2 } from "lucide-react";
import { useTribune } from "@/components/tribune/tribune-provider";
import { useT } from "@/lib/i18n/client";
import { emptyTribune } from "@/lib/tribune";

/** Removes every on-device favourite at once. */
export function ClearTribune() {
  const tr = useT();
  const store = useTribune();
  if (!store) return null;
  return (
    <button
      type="button"
      onClick={() => store.replace(emptyTribune())}
      className="bg-card hover:bg-muted text-muted-foreground hover:text-foreground inline-flex h-9 items-center gap-1.5 rounded-md border px-3 text-sm font-medium transition-colors duration-150"
    >
      <Trash2 className="size-4" aria-hidden />
      {tr.tribune.clear}
    </button>
  );
}
