"use client";

import { ErrorState } from "@/components/ui/states";
import { useT } from "@/lib/i18n/client";

export default function GlobalError({ reset }: { error: Error; reset: () => void }) {
  return <ErrorState labels={useT().states} onRetry={reset} />;
}
