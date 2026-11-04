import { Search } from "lucide-react";
import { t } from "@/lib/i18n";

/** Plain GET form: works without JavaScript and lands on /search?q=. */
export function SearchForm({
  defaultValue = "",
  shortcutSpace = false,
}: {
  defaultValue?: string;
  /** Leaves room on the right for the Ctrl+K hint (header only). */
  shortcutSpace?: boolean;
}) {
  return (
    <form
      action="/search"
      role="search"
      aria-label={t().nav.searchLabel}
      className="relative w-full"
    >
      <label htmlFor="site-search" className="sr-only">
        {t().nav.searchLabel}
      </label>
      <Search
        className="text-muted-foreground pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2"
        aria-hidden
      />
      <input
        id="site-search"
        name="q"
        type="search"
        minLength={2}
        defaultValue={defaultValue}
        placeholder={t().nav.searchPlaceholder}
        className={`bg-card placeholder:text-muted-foreground h-10 w-full rounded-md border pr-3 pl-9 text-sm ${shortcutSpace ? "sm:pr-16" : ""}`}
      />
    </form>
  );
}
