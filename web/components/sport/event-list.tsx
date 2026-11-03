import { ChevronRight } from "lucide-react";
import Link from "next/link";
import { EventItem } from "@/components/sport/event-item";
import { TeamBadge } from "@/components/sport/team-badge";
import { groupByDay } from "@/lib/events";
import { formatDay } from "@/lib/format";
import { intlLocale, t } from "@/lib/i18n";
import type { Competition, SportEvent } from "@/lib/types";

/** A titled card holding event rows (used per competition, or per day). */
export function EventCard({
  title,
  href,
  subtitle,
  events,
  showRound,
  competition,
  heading: Heading = "h3",
}: {
  title: string;
  href?: string;
  subtitle?: string;
  events: SportEvent[];
  showRound?: boolean;
  /** Shows the league badge in the header. */
  competition?: Pick<Competition, "name" | "logo_url">;
  heading?: "h2" | "h3";
}) {
  return (
    <section className="bg-card overflow-hidden rounded-xl border">
      <header className="flex items-center gap-2.5 border-b px-3 py-2">
        {competition ? (
          <TeamBadge team={competition} size="sm" variant="competition" />
        ) : null}
        <div className="min-w-0 flex-1">
          <Heading className="truncate text-sm font-semibold">
            {href ? (
              <Link
                href={href}
                className="hover:text-primary transition-colors duration-150"
              >
                {title}
              </Link>
            ) : (
              title
            )}
          </Heading>
          {subtitle ? (
            <p className="text-muted-foreground truncate text-xs">{subtitle}</p>
          ) : null}
        </div>
        <span className="text-muted-foreground num text-xs">
          {t().today.matchCount(events.length)}
        </span>
        {href ? (
          <Link
            href={href}
            aria-hidden
            tabIndex={-1}
            className="text-muted-foreground hover:text-foreground -mr-1 p-1"
          >
            <ChevronRight className="size-4" />
          </Link>
        ) : null}
      </header>
      <ul className="divide-y">
        {events.map((event) => (
          <EventItem key={event.id} event={event} showRound={showRound} />
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
          title={formatDay(day, undefined, intlLocale())}
          events={dayEvents}
          showRound
          heading="h2"
        />
      ))}
    </div>
  );
}
