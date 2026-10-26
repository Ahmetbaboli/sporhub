"use client";

import { ErrorState } from "@/components/ui/states";

export default function GlobalError({ reset }: { error: Error; reset: () => void }) {
  return <ErrorState onRetry={reset} />;
}
