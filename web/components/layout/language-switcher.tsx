import { setLocaleAction } from "@/app/actions/account";
import { getLocale, t } from "@/lib/i18n";
import { LOCALES } from "@/lib/i18n/config";
import { cn } from "@/lib/utils";

/** TR | EN toggle. A plain form posting to a server action, so it works without JavaScript. */
export function LanguageSwitcher() {
  const active = getLocale();
  const m = t();
  return (
    <form
      action={setLocaleAction}
      className="flex items-center"
      aria-label={m.nav.language}
    >
      {LOCALES.map((locale) => (
        <button
          key={locale}
          type="submit"
          name="locale"
          value={locale}
          lang={locale}
          aria-pressed={locale === active}
          title={m.languages[locale]}
          className={cn(
            "h-8 rounded-md px-2 text-xs font-semibold uppercase",
            locale === active
              ? "bg-muted text-foreground"
              : "text-muted-foreground hover:bg-muted",
          )}
        >
          {locale}
        </button>
      ))}
    </form>
  );
}
