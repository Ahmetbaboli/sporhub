"use client";

import { useId, useState } from "react";
import { cn } from "@/lib/utils";

export interface LeagueTab {
  id: string;
  label: string;
  badge: React.ReactNode;
  panel: React.ReactNode;
}

/**
 * League switcher for the home widgets (Mackolik-style mini tables). Panels are rendered on
 * the server; this only decides which one is visible. Arrow keys move between tabs.
 */
export function LeagueTabs({ tabs, label }: { tabs: LeagueTab[]; label: string }) {
  const [active, setActive] = useState(0);
  const base = useId();
  if (tabs.length === 0) return null;
  const move = (to: number) => {
    const next = (to + tabs.length) % tabs.length;
    setActive(next);
    document.getElementById(`${base}-tab-${next}`)?.focus();
  };
  return (
    <div>
      <div
        role="tablist"
        aria-label={label}
        className="scroll-strip flex gap-1 overflow-x-auto border-b px-2 pt-2"
      >
        {tabs.map((tab, i) => (
          <button
            key={tab.id}
            id={`${base}-tab-${i}`}
            type="button"
            role="tab"
            aria-selected={i === active}
            aria-controls={`${base}-panel-${i}`}
            tabIndex={i === active ? 0 : -1}
            onClick={() => setActive(i)}
            onKeyDown={(e) => {
              if (e.key === "ArrowRight") move(i + 1);
              if (e.key === "ArrowLeft") move(i - 1);
            }}
            title={tab.label}
            className={cn(
              "-mb-px inline-flex h-10 shrink-0 items-center gap-1.5 border-b-2 px-2 text-xs font-semibold transition-colors duration-150",
              i === active
                ? "border-primary text-foreground"
                : "text-muted-foreground hover:text-foreground border-transparent",
            )}
          >
            {tab.badge}
            <span className="max-w-24 truncate">{tab.label}</span>
          </button>
        ))}
      </div>
      {tabs.map((tab, i) => (
        <div
          key={tab.id}
          id={`${base}-panel-${i}`}
          role="tabpanel"
          aria-labelledby={`${base}-tab-${i}`}
          hidden={i !== active}
        >
          {tab.panel}
        </div>
      ))}
    </div>
  );
}
