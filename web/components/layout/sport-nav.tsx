"use client";

import { GitCompareArrows, Newspaper, Star } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useT } from "@/lib/i18n/client";
import { templateFor } from "@/lib/sports";
import type { Sport } from "@/lib/types";
import { cn } from "@/lib/utils";

export function SportNav({ sports }: { sports: Sport[] }) {
  const tr = useT();
  const pathname = usePathname();
  const items = [
    { href: "/", label: tr.nav.home, Icon: null },
    { href: "/news", label: tr.nav.news, Icon: Newspaper },
    ...sports.map((s) => ({
      href: `/${s.slug}`,
      label: s.name,
      Icon: templateFor(s.slug).icon,
    })),
    { href: "/tribun", label: tr.tribune.title, Icon: Star },
    { href: "/compare", label: tr.compare.title, Icon: GitCompareArrows },
  ];

  return (
    <nav
      aria-label={tr.nav.primary}
      className="scroll-strip order-4 -mb-2 w-full overflow-x-auto"
    >
      <ul className="flex gap-1 pb-2">
        {items.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.split("/")[1] === item.href.slice(1);
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "inline-flex h-9 items-center rounded-md px-3 text-sm font-medium whitespace-nowrap transition-colors duration-150",
                  active
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                {item.Icon ? <item.Icon className="mr-1.5 size-4" aria-hidden /> : null}
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
