import { tr } from "@/lib/i18n/tr";

export function Footer() {
  return (
    <footer className="text-muted-foreground border-t text-sm">
      <div className="mx-auto flex max-w-5xl flex-col gap-1 px-4 py-6 sm:flex-row sm:justify-between">
        <p>
          <span className="font-display text-foreground text-base font-semibold uppercase">
            {tr.app.name}
          </span>{" "}
          — {tr.app.tagline}
        </p>
        <p>{tr.footer.openSource}</p>
      </div>
      <p className="mx-auto max-w-5xl px-4 pb-6 text-xs">{tr.footer.note}</p>
    </footer>
  );
}
