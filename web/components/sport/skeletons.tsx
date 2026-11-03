import { LoadingRegion, Skeleton } from "@/components/ui/skeleton";
import { t } from "@/lib/i18n";

export function TitleSkeleton() {
  return (
    <div className="mb-6 space-y-2">
      <Skeleton className="h-9 w-64 max-w-full" />
      <Skeleton className="h-4 w-80 max-w-full" />
    </div>
  );
}

export function EventCardSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="bg-card overflow-hidden rounded-xl border">
      <div className="flex items-center gap-2.5 border-b px-3 py-2.5">
        <Skeleton className="size-7 rounded-lg" />
        <Skeleton className="h-4 w-40" />
      </div>
      <div className="divide-y">
        {Array.from({ length: rows }, (_, i) => (
          <div
            key={i}
            className="grid grid-cols-[2.75rem_minmax(0,1fr)_5.25rem_minmax(0,1fr)_2.25rem] items-center gap-1.5 px-3 py-3 sm:grid-cols-[4rem_minmax(0,1fr)_5.5rem_minmax(0,1fr)_2.25rem] sm:gap-3"
          >
            <Skeleton className="h-4 w-10" />
            <Skeleton className="ml-auto h-4 w-24" />
            <Skeleton className="mx-auto h-7 w-14" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="size-6" />
          </div>
        ))}
      </div>
    </div>
  );
}

/** Suspense fallback for a block of event cards (no page title: the page renders its own). */
export function EventCardsSkeleton({ cards = 2 }: { cards?: number }) {
  return (
    <LoadingRegion label={t().states.loading}>
      <div className="space-y-4">
        {Array.from({ length: cards }, (_, i) => (
          <EventCardSkeleton key={i} />
        ))}
      </div>
    </LoadingRegion>
  );
}

/** Whole-page skeleton, used by routes that never 404 (search). */
export function EventListSkeleton({ cards = 2 }: { cards?: number }) {
  return (
    <>
      <TitleSkeleton />
      <EventCardsSkeleton cards={cards} />
    </>
  );
}

/** Suspense fallback for a table block. */
export function TableSkeleton({ rows = 10 }: { rows?: number }) {
  return (
    <LoadingRegion label={t().states.loading}>
      <div className="bg-card space-y-3 rounded-lg border p-3">
        {Array.from({ length: rows }, (_, i) => (
          <Skeleton key={i} className="h-6 w-full" />
        ))}
      </div>
    </LoadingRegion>
  );
}

/** News feed placeholder: same cover + text geometry as the real cards, so nothing jumps. */
export function NewsFeedSkeleton({ items = 5 }: { items?: number }) {
  return (
    <LoadingRegion label={t().states.loading}>
      <div className="grid gap-3">
        {Array.from({ length: items }, (_, i) => (
          <div key={i} className="bg-card flex gap-3 rounded-xl border p-3 sm:gap-4">
            <Skeleton className="aspect-[4/3] w-24 shrink-0 rounded-lg sm:aspect-[16/10] sm:w-44" />
            <div className="flex-1 space-y-2 py-1">
              <Skeleton className="h-3 w-40" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </div>
          </div>
        ))}
      </div>
    </LoadingRegion>
  );
}
