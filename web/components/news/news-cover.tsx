"use client";

import { CircleDot, Flag, Goal, Newspaper, type LucideIcon } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

/**
 * News visual. Publishers' feeds do not license their photos to us, so a story shows its own
 * image only when the API carries one (e.g. an admin-entered item) and it loads; otherwise a
 * designed cover for its sport. Never a stock or unrelated photo, never a broken image.
 */
type Look = { Icon: LucideIcon; tint: string; Pattern: () => React.ReactElement };

function Pitch() {
  return (
    <g fill="none" stroke="currentColor" strokeWidth="1.2">
      <rect x="8" y="8" width="144" height="74" rx="2" />
      <path d="M80 8v74" />
      <circle cx="80" cy="45" r="13" />
      <rect x="8" y="27" width="20" height="36" />
      <rect x="132" y="27" width="20" height="36" />
    </g>
  );
}

function Court() {
  return (
    <g fill="none" stroke="currentColor" strokeWidth="1.2">
      <rect x="8" y="8" width="144" height="74" rx="2" />
      <path d="M80 8v74" />
      <circle cx="80" cy="45" r="11" />
      <path d="M8 22h22a23 23 0 0 1 0 46H8M152 22h-22a23 23 0 0 0 0 46h22" />
    </g>
  );
}

function Track() {
  return (
    <g fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round">
      <path d="M14 70c18 0 22-40 46-40s20 26 42 26 18-34 44-34" />
      <path d="M14 76c22 0 26-38 46-38s22 26 42 26 22-34 44-34" opacity=".5" />
      <path
        d="M128 12h6v6h-6zm6 6h6v6h-6zm6-6h6v6h-6z"
        fill="currentColor"
        stroke="none"
      />
    </g>
  );
}

function Lines() {
  return (
    <g fill="none" stroke="currentColor" strokeWidth="1.2" opacity=".8">
      <path d="M-10 90 60 0M10 90 80 0M30 90 100 0M50 90 120 0M70 90 140 0M90 90 160 0" />
    </g>
  );
}

const LOOKS: Record<string, Look> = {
  football: { Icon: Goal, tint: "text-primary", Pattern: Pitch },
  basketball: { Icon: CircleDot, tint: "text-accent", Pattern: Court },
  "formula-1": { Icon: Flag, tint: "text-live", Pattern: Track },
};
const GENERAL: Look = { Icon: Newspaper, tint: "text-primary", Pattern: Lines };

export function NewsCover({
  sport,
  imageUrl,
  caption,
  className,
  size = "md",
}: {
  sport: string | null;
  imageUrl?: string | null;
  /** Large covers print this (the publisher's name) as their typographic motif. */
  caption?: string;
  className?: string;
  size?: "sm" | "md" | "lg";
}) {
  const [failed, setFailed] = useState(false);
  const look = (sport && LOOKS[sport]) || GENERAL;
  return (
    <div
      aria-hidden
      className={cn("bg-muted zoom-media relative overflow-hidden", className)}
    >
      {imageUrl && !failed ? (
        // eslint-disable-next-line @next/next/no-img-element -- publisher-hosted image
        <img
          src={imageUrl}
          alt=""
          loading="lazy"
          decoding="async"
          onError={() => setFailed(true)}
          className="absolute inset-0 size-full object-cover"
        />
      ) : (
        <div className={cn("absolute inset-0", look.tint)}>
          <div className="absolute inset-0 bg-[radial-gradient(120%_90%_at_100%_0%,currentColor_0%,transparent_60%)] opacity-[0.16]" />
          <svg
            viewBox="0 0 160 90"
            preserveAspectRatio="xMidYMid slice"
            className="absolute inset-0 size-full opacity-25"
          >
            <look.Pattern />
          </svg>
          <div
            className={cn(
              "absolute flex items-center",
              size === "lg"
                ? "bottom-4 left-4 gap-3"
                : size === "md"
                  ? "bottom-3 left-3 gap-2"
                  : "bottom-2 left-2",
            )}
          >
            <look.Icon
              className={cn(
                "shrink-0 opacity-90",
                size === "lg" ? "size-9" : size === "md" ? "size-6" : "size-4",
              )}
            />
            {caption && size === "lg" ? (
              <span className="font-display text-4xl leading-none font-bold tracking-tight opacity-80 sm:text-5xl">
                {caption}
              </span>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
