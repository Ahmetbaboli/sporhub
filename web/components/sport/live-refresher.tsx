"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

const REFRESH_MS = 60_000;

/**
 * Re-renders the page from the server once a minute while it shows live games (the API
 * client caches for 60 s, so this matches how often scores can change here). Paused while
 * the tab is hidden.
 */
export function LiveRefresher({ active }: { active: boolean }) {
  const router = useRouter();
  useEffect(() => {
    if (!active) return;
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") router.refresh();
    }, REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [active, router]);
  return null;
}
