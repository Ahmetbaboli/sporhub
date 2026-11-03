"use client";

import { useState } from "react";
import type { Team } from "@/lib/types";
import { badgeCode, cn } from "@/lib/utils";

const SIZES = {
  sm: { box: "size-7 text-[10px]", pad: "p-0.5", px: 28 },
  md: { box: "size-9 text-[11px]", pad: "p-0.5", px: 36 },
  lg: { box: "size-14 text-sm", pad: "p-1", px: 56 },
} as const;

/**
 * Club/league badge. The provider's own crest is shown only when the API serves it (owner
 * opted in with SHOW_PROVIDER_IMAGES); otherwise, or when the image fails, a drawn badge with
 * the provider's short code (GAL, ARS) or initials. The box size is fixed so nothing shifts.
 */
export function TeamBadge({
  team,
  size = "md",
  variant = "team",
}: {
  team: Pick<Team, "name" | "logo_url"> & { short_name?: string | null };
  size?: keyof typeof SIZES;
  variant?: "team" | "competition";
}) {
  const [failed, setFailed] = useState(false);
  const { box, pad, px } = SIZES[size];
  const frame = cn(
    "inline-flex shrink-0 items-center justify-center overflow-hidden",
    variant === "competition" ? "rounded-xl" : "rounded-lg",
    box,
  );

  if (team.logo_url && !failed) {
    return (
      // Crests come from the provider's host. A faint light outline (dark theme) keeps dark
      // crests visible without a plate; padding is fixed (a % would follow the parent).
      <span aria-hidden className={cn(frame, pad)}>
        {/* eslint-disable-next-line @next/next/no-img-element -- crests come from arbitrary hosts */}
        <img
          src={team.logo_url}
          alt=""
          width={px}
          height={px}
          loading="lazy"
          decoding="async"
          onError={() => setFailed(true)}
          className="size-full object-contain dark:drop-shadow-[0_0_1px_rgba(255,255,255,0.45)]"
        />
      </span>
    );
  }
  return (
    <span
      aria-hidden
      className={cn(
        frame,
        "bg-muted text-foreground/85 border font-bold tracking-tight",
        variant === "competition" && "border-t-primary border-t-2",
      )}
    >
      {badgeCode(team)}
    </span>
  );
}
