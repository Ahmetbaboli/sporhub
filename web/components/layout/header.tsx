import Link from "next/link";
import { SearchForm } from "@/components/layout/search-form";
import { SportNav } from "@/components/layout/sport-nav";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { api } from "@/lib/api";
import { tr } from "@/lib/i18n/tr";
import type { Sport } from "@/lib/types";

const FALLBACK_SPORTS: Sport[] = [{ id: 1, slug: "football", name: tr.sports.football }];

async function loadSports(): Promise<Sport[]> {
  try {
    return (await api.sports()).items;
  } catch {
    // The header must render even when the API is down.
    return FALLBACK_SPORTS;
  }
}

export async function Header() {
  const sports = await loadSports();
  return (
    <header className="bg-background/90 sticky top-0 z-40 border-b backdrop-blur">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-2">
        <Link
          href="/"
          className="font-display text-primary text-2xl leading-none font-bold tracking-tight uppercase"
        >
          Just<span className="text-accent">Sport</span>
        </Link>
        <div className="order-3 w-full sm:order-2 sm:w-64 sm:flex-none md:ml-auto">
          <SearchForm />
        </div>
        <div className="order-2 ml-auto sm:order-3 sm:ml-0">
          <ThemeToggle />
        </div>
        <SportNav sports={sports} />
      </div>
    </header>
  );
}
