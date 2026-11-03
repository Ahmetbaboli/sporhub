import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

const PROVIDER_CODE = /^[A-Z0-9]{2,4}$/;

/** Badge text: the provider's own short code (TLA such as "GAL") when it has one, else initials. */
export function badgeCode(team: { name: string; short_name?: string | null }): string {
  const code = team.short_name?.trim().toUpperCase();
  return code && PROVIDER_CODE.test(code) ? code : initials(team.name);
}

/** "Manchester City FC" -> "MC"; used when a crest is missing or fails to load. */
export function initials(name: string): string {
  const words = name
    .replace(/\b(FC|AFC|CF|SK|FK|AC|AS|SS|US|SC|SV|FSV)\b/g, "")
    .split(/[\s.-]+/)
    .filter((w) => w && !/^\d+$/.test(w));
  const letters =
    words.length > 1
      ? words.slice(0, 2).map((w) => w[0])
      : [(words[0] ?? name).slice(0, 2)];
  return letters.join("").toUpperCase();
}
