import Link from "next/link";
import { tr } from "@/lib/i18n/tr";
import { cn } from "@/lib/utils";

const BUTTON = "inline-flex h-10 items-center rounded-md border px-4 text-sm font-medium";

/** Link-based pager (works without JS). `hrefFor` builds the URL for a page number. */
export function Pagination({
  page,
  pageSize,
  total,
  hrefFor,
}: {
  page: number;
  pageSize: number;
  total: number;
  hrefFor: (page: number) => string;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (pages <= 1) return null;
  return (
    <nav
      aria-label={tr.pagination.label}
      className="mt-4 flex items-center justify-between gap-3"
    >
      {page > 1 ? (
        <Link
          href={hrefFor(page - 1)}
          rel="prev"
          className={cn(BUTTON, "hover:bg-muted")}
        >
          {tr.pagination.previous}
        </Link>
      ) : (
        <span aria-hidden />
      )}
      <span className="text-muted-foreground text-sm">
        {tr.pagination.page(page, pages)}
      </span>
      {page < pages ? (
        <Link
          href={hrefFor(page + 1)}
          rel="next"
          className={cn(BUTTON, "hover:bg-muted")}
        >
          {tr.pagination.next}
        </Link>
      ) : (
        <span aria-hidden />
      )}
    </nav>
  );
}
