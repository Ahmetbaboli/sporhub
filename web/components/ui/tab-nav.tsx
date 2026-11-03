import Link from "next/link";
import { ActiveTabScroller } from "@/components/ui/active-tab-scroller";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export interface TabItem {
  id: string;
  label: string;
  href: string;
}

/**
 * Server-rendered tabs: each tab is a link, the active one carries aria-current. On narrow
 * screens the strip scrolls sideways without a scrollbar and keeps the active tab in view.
 */
export function TabNav({
  tabs,
  active,
  label = t().competition.tabsLabel,
}: {
  tabs: TabItem[];
  active: string;
  label?: string;
}) {
  return (
    <nav aria-label={label} className="relative mb-4 border-b">
      <ActiveTabScroller />
      <ul className="scroll-strip flex gap-1 overflow-x-auto">
        {tabs.map((tab) => (
          <li key={tab.id} className="shrink-0">
            <Link
              href={tab.href}
              aria-current={tab.id === active ? "page" : undefined}
              className={cn(
                "-mb-px inline-flex h-11 items-center border-b-2 px-3.5 text-sm font-semibold whitespace-nowrap transition-colors duration-150",
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
