import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** "Manchester City FC" -> "MC"; used when a crest is missing or fails to load. */
export function initials(name: string): string {
  const words = name
    .replace(/\b(FC|AFC|CF|SK|FK|AC|AS|SS|US|SC|1\.)\b/g, "")
    .split(/[\s.-]+/)
    .filter(Boolean);
  const letters =
    words.length > 1 ? words.slice(0, 2).map((w) => w[0]) : [name.slice(0, 2)];
  return letters.join("").toUpperCase();
}
