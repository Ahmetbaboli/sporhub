import Link from "next/link";
import { UserMenu } from "@/components/account/user-menu";
import { LanguageSwitcher } from "@/components/layout/language-switcher";
import { PalettePicker } from "@/components/layout/palette-picker";
import { QuickSearch } from "@/components/layout/quick-search";
import { SearchForm } from "@/components/layout/search-form";
import { SportNav } from "@/components/layout/sport-nav";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { api } from "@/lib/api";
import { t } from "@/lib/i18n";
import type { Sport } from "@/lib/types";

async function loadSports(): Promise<Sport[]> {
  try {
    return (await api.sports()).items;
  } catch {
    // The header must render even when the API is down.
    return [{ id: 1, slug: "football", name: t().sports.football }];
  }
}

export async function Header() {
  const sports = await loadSports();
  return (
    <header className="bg-background/90 sticky top-0 z-40 border-b backdrop-blur">
      <div className="mx-auto flex max-w-[80rem] flex-wrap items-center gap-x-4 gap-y-2 px-4 py-2 sm:px-6">
        <Link
          href="/"
          aria-label="Just Sport"
          className="font-display text-[1.7rem] leading-none font-bold tracking-tight uppercase"
        >
          <span className="text-primary">Just</span>
          <span className="text-accent">Sport</span>
        </Link>
        <div className="relative order-3 w-full sm:order-2 sm:w-72 sm:flex-none md:ml-auto">
          <SearchForm shortcutSpace />
          <QuickSearch />
        </div>
        <div className="order-2 ml-auto flex items-center sm:order-3 sm:ml-0">
          <LanguageSwitcher />
          <PalettePicker />
          <ThemeToggle />
          <UserMenu />
        </div>
        <SportNav sports={sports} />
      </div>
    </header>
  );
}
