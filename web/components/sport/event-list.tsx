import Link from "next/link";
import { EventRow } from "@/components/sport/event-row";
import { groupByDay } from "@/lib/events";
import { formatDay } from "@/lib/format";
import type { Competition, SportEvent } from "@/lib/types";

/** A titled card holding event rows (used per competition). */
export function EventCard({
  title,
  href,
  subtitle,
  events,
  showRound,
  heading: Heading = "h3",
}: {
  title: string;
  href?: string;
  subtitle?: string;
  events: SportEvent[];
  showRound?: boolean;
  heading?: "h2" | "h3";
}) {
  return (
    <section className="bg-card overflow-hidden rounded-lg border">
      <header className="bg-muted/60 flex items-baseline justify-between gap-2 border-b px-3 py-2">
        <Heading className="font-display text-lg font-semibold tracking-wide uppercase">
          {href ? (
            <Link href={href} className="hover:underline">
              {title}
            </Link>
          ) : (
            title
          )}
        </Heading>
        {subtitle ? (
          <span className="text-muted-foreground text-xs">{subtitle}</span>
        ) : null}
      </header>
      <ul className="divide-y">
        {events.map((event) => (
          <EventRow key={event.id} event={event} showRound={showRound} />
        ))}
      </ul>
    </section>
  );
}

export function competitionHref(c: Pick<Competition, "sport_slug" | "slug">): string {
  return `/${c.sport_slug}/${c.slug}`;
}

/** Events grouped under day headings (fixtures / results lists). */
export function DayGroupedEvents({ events }: { events: SportEvent[] }) {
  return (
    <div className="space-y-4">
      {groupByDay(events).map(({ day, events: dayEvents }) => (
        <EventCard
          key={day}
          title={formatDay(day)}
          events={dayEvents}
          showRound
          heading="h2"
        />
      ))}
    </div>
  );
}
