"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

/**
 * Title whose words rise out of a blur one after another (CSS `.split-word`). The text stays
 * one readable string for assistive tech; `accent` words are set in the italic serif.
 */
export function SplitWords({
  text,
  accent,
  className,
}: {
  text: string;
  /** Trailing words to set in the accent face ("karşılaşmaları"). */
  accent?: string;
  className?: string;
}) {
  const plain = text.split(" ").filter(Boolean);
  const fancy = (accent ?? "").split(" ").filter(Boolean);
  const words = [
    ...plain.map((w) => ({ w, accent: false })),
    ...fancy.map((w) => ({ w, accent: true })),
  ];
  return (
    <span className={className} aria-label={[text, accent].filter(Boolean).join(" ")}>
      {words.map(({ w, accent: isAccent }, i) => (
        <span
          key={`${w}-${i}`}
          aria-hidden
          className={cn(
            "split-word",
            isAccent &&
              "text-primary font-serif font-medium tracking-normal normal-case italic",
          )}
          style={{ "--i": i } as React.CSSProperties}
        >
          {w}
          {i < words.length - 1 ? " " : null}
        </span>
      ))}
    </span>
  );
}

const REVEAL_FALLBACK_MS = 1200;

/** Fades its children up out of a light blur the first time they scroll into view. */
export function Reveal({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [shown, setShown] = useState(false);
  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    if (!("IntersectionObserver" in window)) {
      const raf = requestAnimationFrame(() => setShown(true));
      return () => cancelAnimationFrame(raf);
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setShown(true);
          observer.disconnect();
        }
      },
      { rootMargin: "0px 0px -8% 0px" },
    );
    observer.observe(node);
    // Safety net: content must never stay hidden if the observer does not fire.
    const fallback = window.setTimeout(() => setShown(true), REVEAL_FALLBACK_MS);
    return () => {
      observer.disconnect();
      window.clearTimeout(fallback);
    };
  }, []);
  return (
    <div ref={ref} className={cn("reveal", shown && "is-in", className)}>
      {children}
    </div>
  );
}

const COUNT_MS = 900;

/** A real number that counts up once when it scrolls into view (static for reduced motion). */
export function CountUp({ value, className }: { value: number; className?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [shown, setShown] = useState<number | null>(null);
  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let frame = 0;
    const run = () => {
      if (still) return setShown(value);
      const start = performance.now();
      const tick = (now: number) => {
        const p = Math.min(1, (now - start) / COUNT_MS);
        setShown(Math.round(value * (1 - (1 - p) ** 3)));
        if (p < 1) frame = requestAnimationFrame(tick);
      };
      frame = requestAnimationFrame(tick);
    };
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        observer.disconnect();
        run();
      }
    });
    observer.observe(node);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [value]);
  return (
    <span ref={ref} className={className}>
      {/* The final value is in the markup for no-JS and screen readers. */}
      <span aria-hidden>{shown ?? value}</span>
      <span className="sr-only">{value}</span>
    </span>
  );
}
