import { Flag } from "lucide-react";
import { CIRCUITS } from "@/lib/circuits";
import { t } from "@/lib/i18n";
import { cn } from "@/lib/utils";

/**
 * Track outline for a Jolpica circuitId (generated, MIT data; see lib/circuits.ts). A circuit
 * without an outline gets a neutral flag tile rather than a made-up drawing.
 */
export function CircuitMap({
  circuitId,
  name,
  className,
  strokeWidth = 2.4,
}: {
  circuitId: string | undefined;
  name: string;
  className?: string;
  strokeWidth?: number;
}) {
  const outline = circuitId ? CIRCUITS[circuitId] : undefined;
  if (!outline) {
    return (
      <div
        role="img"
        aria-label={t().f1.noCircuit}
        className={cn(
          "text-muted-foreground flex items-center justify-center",
          className,
        )}
      >
        <Flag className="size-8" aria-hidden />
      </div>
    );
  }
  return (
    <svg
      viewBox={outline.viewBox}
      role="img"
      aria-label={t().f1.circuitOf(name)}
      className={cn("overflow-visible", className)}
      preserveAspectRatio="xMidYMid meet"
    >
      <path
        d={outline.path}
        fill="none"
        stroke="currentColor"
        strokeOpacity="0.18"
        strokeWidth={strokeWidth * 3}
        strokeLinejoin="round"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
      />
      <path
        d={outline.path}
        fill="none"
        stroke="currentColor"
        strokeWidth={strokeWidth}
        strokeLinejoin="round"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
