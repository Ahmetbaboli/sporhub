"use client";

import { Check, Palette as PaletteIcon } from "lucide-react";
import { useRef, useSyncExternalStore } from "react";
import { tr } from "@/lib/i18n/tr";
import {
  DEFAULT_PALETTE,
  PALETTE_STORAGE_KEY,
  PALETTE_SWATCHES,
  PALETTES,
  parsePalette,
  type Palette,
} from "@/lib/palettes";
import { cn } from "@/lib/utils";

const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function current(): Palette {
  return parsePalette(document.documentElement.dataset.palette);
}

function apply(palette: Palette) {
  const root = document.documentElement;
  if (palette === DEFAULT_PALETTE) delete root.dataset.palette;
  else root.dataset.palette = palette;
  try {
    localStorage.setItem(PALETTE_STORAGE_KEY, palette);
  } catch {
    // Private mode: the choice still applies for this page view.
  }
  listeners.forEach((l) => l());
}

export function PalettePicker() {
  const active = useSyncExternalStore(subscribe, current, () => DEFAULT_PALETTE);
  const details = useRef<HTMLDetailsElement>(null);

  return (
    <details ref={details} className="relative">
      <summary
        aria-label={tr.nav.palette}
        title={tr.nav.palette}
        className="hover:bg-muted inline-flex size-10 cursor-pointer list-none items-center justify-center rounded-md [&::-webkit-details-marker]:hidden"
      >
        <PaletteIcon className="size-5" aria-hidden />
      </summary>
      <div
        role="group"
        aria-label={tr.nav.palette}
        className="bg-card absolute right-0 z-50 mt-1 w-48 rounded-lg border p-1 shadow-lg"
      >
        {PALETTES.map((palette) => (
          <button
            key={palette}
            type="button"
            aria-pressed={active === palette}
            onClick={() => {
              apply(palette);
              details.current?.removeAttribute("open");
            }}
            className={cn(
              "hover:bg-muted flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm",
              active === palette && "font-semibold",
            )}
          >
            <span
              aria-hidden
              className="size-4 rounded-full border"
              style={{ background: PALETTE_SWATCHES[palette] }}
            />
            <span className="flex-1">{tr.palettes[palette]}</span>
            {active === palette ? <Check className="size-4" aria-hidden /> : null}
          </button>
        ))}
      </div>
    </details>
  );
}
