import Link from "next/link";
import { tr } from "@/lib/i18n/tr";
import { cn } from "@/lib/utils";

export interface TabItem {
  id: string;
  label: string;
  href: string;
}

/** Server-rendered tabs: each tab is a link, the active one carries aria-current. */
export function TabNav({ tabs, active }: { tabs: TabItem[]; active: string }) {
  return (
    <nav aria-label={tr.competition.tabsLabel} className="mb-4 overflow-x-auto border-b">
      <ul className="flex gap-1">
        {tabs.map((tab) => (
          <li key={tab.id}>
            <Link
              href={tab.href}
              aria-current={tab.id === active ? "page" : undefined}
              className={cn(
                "-mb-px inline-flex h-11 items-center border-b-2 px-4 text-sm font-semibold whitespace-nowrap",
                tab.id === active
                  ? "border-primary text-foreground"
                  : "text-muted-foreground hover:text-foreground border-transparent",
              )}
            >
              {tab.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
