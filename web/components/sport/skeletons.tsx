import { LoadingRegion, Skeleton } from "@/components/ui/skeleton";
import { tr } from "@/lib/i18n/tr";

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
    <div className="bg-card overflow-hidden rounded-lg border">
      <div className="bg-muted/60 border-b px-3 py-3">
        <Skeleton className="h-5 w-40" />
      </div>
      <div className="divide-y">
        {Array.from({ length: rows }, (_, i) => (
          <div
            key={i}
            className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 px-3 py-3.5"
          >
            <Skeleton className="ml-auto h-5 w-24" />
            <Skeleton className="h-6 w-14" />
            <Skeleton className="h-5 w-24" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function EventListSkeleton({ cards = 2 }: { cards?: number }) {
  return (
    <LoadingRegion label={tr.states.loading}>
      <TitleSkeleton />
      <div className="space-y-4">
        {Array.from({ length: cards }, (_, i) => (
          <EventCardSkeleton key={i} />
        ))}
      </div>
    </LoadingRegion>
  );
}

export function TableSkeleton({ rows = 10 }: { rows?: number }) {
  return (
    <LoadingRegion label={tr.states.loading}>
      <TitleSkeleton />
      <Skeleton className="mb-4 h-11 w-full max-w-md" />
      <div className="bg-card space-y-3 rounded-lg border p-3">
        {Array.from({ length: rows }, (_, i) => (
          <Skeleton key={i} className="h-6 w-full" />
        ))}
      </div>
    </LoadingRegion>
  );
}
