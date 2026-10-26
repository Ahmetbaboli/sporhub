import { LoadingRegion, Skeleton } from "@/components/ui/skeleton";
import { tr } from "@/lib/i18n/tr";

export default function Loading() {
  return (
    <LoadingRegion label={tr.states.loading}>
      <Skeleton className="h-10 w-48" />
      <Skeleton className="mt-4 h-10 w-full max-w-xl" />
      <Skeleton className="mt-6 h-48 w-full" />
    </LoadingRegion>
  );
}
