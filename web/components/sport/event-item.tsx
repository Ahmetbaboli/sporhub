import { EventRow } from "@/components/sport/event-row";
import { RaceRow } from "@/components/sport/race-row";
import type { SportEvent } from "@/lib/types";

/** Picks the right card for an event kind: matches get a scoreline, races get a podium. */
export function EventItem({
  event,
  showRound,
}: {
  event: SportEvent;
  showRound?: boolean;
}) {
  if (event.kind === "race") return <RaceRow event={event} />;
  return <EventRow event={event} showRound={showRound} />;
}
