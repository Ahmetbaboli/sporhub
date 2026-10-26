import { cn } from "@/lib/utils";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div aria-hidden className={cn("bg-muted animate-pulse rounded-md", className)} />
  );
}

/** Wraps skeleton content so assistive tech announces a single loading state. */
export function LoadingRegion({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div role="status" aria-busy="true" aria-live="polite">
      <span className="sr-only">{label}</span>
      {children}
    </div>
  );
}
