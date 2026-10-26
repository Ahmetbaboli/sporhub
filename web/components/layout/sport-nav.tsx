"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { tr } from "@/lib/i18n/tr";
import type { Sport } from "@/lib/types";
import { cn } from "@/lib/utils";

export function SportNav({ sports }: { sports: Sport[] }) {
  const pathname = usePathname();
  const items = [
    { href: "/", label: tr.nav.home },
    ...sports.map((s) => ({
      href: `/${s.slug}`,
      label: s.name,
    })),
  ];

  return (
    <nav aria-label={tr.nav.primary} className="order-4 -mb-2 w-full overflow-x-auto">
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
                  "inline-flex h-9 items-center rounded-md px-3 text-sm font-medium whitespace-nowrap",
                  active
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
