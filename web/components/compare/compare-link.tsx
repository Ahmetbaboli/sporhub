import { GitCompareArrows } from "lucide-react";
import Link from "next/link";
import { t } from "@/lib/i18n";

export function CompareLink({ href }: { href: string }) {
  return (
    <Link
      href={href}
      className="hover:bg-muted bg-card inline-flex h-9 items-center gap-1.5 rounded-md border px-3 text-sm font-medium"
    >
      <GitCompareArrows className="size-4" aria-hidden />
      {t().compare.action}
    </Link>
  );
}
