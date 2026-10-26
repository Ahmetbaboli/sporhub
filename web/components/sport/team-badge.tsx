"use client";

import { useState } from "react";
import type { Team } from "@/lib/types";
import { cn, initials } from "@/lib/utils";

const SIZES = {
  sm: "size-6 text-[10px]",
  md: "size-8 text-xs",
  lg: "size-16 text-xl",
} as const;

/** Club crest with an initials fallback for missing or broken logo URLs. */
export function TeamBadge({
  team,
  size = "md",
}: {
  team: Pick<Team, "name" | "logo_url">;
  size?: keyof typeof SIZES;
}) {
  const [failed, setFailed] = useState(false);
  const box = cn(
    "inline-flex shrink-0 items-center justify-center rounded-full",
    SIZES[size],
  );

  if (team.logo_url && !failed) {
    return (
      // eslint-disable-next-line @next/next/no-img-element -- crests come from arbitrary hosts
      <img
        src={team.logo_url}
        alt=""
        loading="lazy"
        onError={() => setFailed(true)}
        className={cn(box, "object-contain")}
      />
    );
  }
  return (
    <span
      aria-hidden
      className={cn(box, "bg-muted text-muted-foreground font-display font-semibold")}
    >
      {initials(team.name)}
    </span>
  );
}
