"use client";

import { useEffect, useRef } from "react";

/**
 * Placed next to a horizontally scrolling `.scroll-strip`: on mount, scrolls the strip (not the
 * page) so the tab marked aria-current="page" is visible, e.g. "Son dakika" at the far end.
 */
export function ActiveTabScroller() {
  const marker = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const parent = marker.current?.parentElement;
    const strip = parent?.querySelector<HTMLElement>(".scroll-strip") ?? parent;
    const active = strip?.querySelector<HTMLElement>('[aria-current="page"]');
    if (!strip || !active) return;
    const offset = active.offsetLeft - (strip.clientWidth - active.offsetWidth) / 2;
    strip.scrollLeft = Math.max(0, offset);
  }, []);
  return <span ref={marker} hidden />;
}
