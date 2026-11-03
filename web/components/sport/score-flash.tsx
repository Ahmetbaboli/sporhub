"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

/**
 * Wraps a score; when `value` really changes between renders (a refresh brought a new score)
 * the element remounts with a one-off highlight. The first render never flashes.
 */
export function ScoreFlash({
  value,
  label,
  className,
  children,
}: {
  value: string;
  label: string;
  className?: string;
  children: React.ReactNode;
}) {
  const [seen, setSeen] = useState(value);
  const [changes, setChanges] = useState(0);
  if (seen !== value) {
    setSeen(value);
    setChanges((n) => n + 1);
  }
  return (
    <span
      key={changes}
      role="img"
      aria-label={label}
      className={cn(className, changes > 0 && "score-flash")}
    >
      {children}
    </span>
  );
}
