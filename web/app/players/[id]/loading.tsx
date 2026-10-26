import { LoadingRegion, Skeleton } from "@/components/ui/skeleton";
import { tr } from "@/lib/i18n/tr";

export default function Loading() {
  return (
    <LoadingRegion label={tr.states.loading}>
      <Skeleton className="h-10 w-72 max-w-full" />
      <Skeleton className="mt-6 h-40 w-full max-w-xl" />
    </LoadingRegion>
  );
}
