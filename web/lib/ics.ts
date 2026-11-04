/** iCalendar (RFC 5545) feed of upcoming events, for "add to calendar". */
import type { SportEvent } from "@/lib/types";

const CRLF = "\r\n";
/** RFC 5545 folds lines longer than 75 octets; 73 characters leaves room for multi-byte. */
const FOLD_AT = 73;
const DEFAULT_DURATION_MS = 2 * 60 * 60 * 1000;
const UID_DOMAIN = "justsport";

export function icsEscape(text: string): string {
  return text
    .replace(/\\/g, "\\\\")
    .replace(/;/g, "\\;")
    .replace(/,/g, "\\,")
    .replace(/\r?\n/g, "\\n");
}

export function icsDate(ms: number): string {
  return new Date(ms)
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\.\d{3}/, "");
}

function fold(line: string): string {
  const chars = [...line];
  if (chars.length <= FOLD_AT) return line;
  const parts: string[] = [];
  for (let i = 0; i < chars.length; i += FOLD_AT)
    parts.push(chars.slice(i, i + FOLD_AT).join(""));
  return parts.join(`${CRLF} `);
}

export function eventTitle(event: SportEvent): string {
  const home = event.participants.find((p) => p.side === "home")?.team?.name;
  const away = event.participants.find((p) => p.side === "away")?.team?.name;
  const name =
    home && away ? `${home} – ${away}` : (event.name ?? event.competition.name);
  return `${name} (${event.competition.name})`;
}

export interface CalendarOptions {
  name: string;
  /** Site origin for links back to the match, e.g. "https://justsport.example". */
  origin: string;
  now?: number;
}

export function buildCalendar(events: SportEvent[], opts: CalendarOptions): string {
  const stamp = icsDate(opts.now ?? Date.now());
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Just Sport//Fixtures//TR",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    `X-WR-CALNAME:${icsEscape(opts.name)}`,
  ];
  for (const event of events) {
    const start = Date.parse(event.start_time);
    const href =
      event.kind === "match" ? `${opts.origin}/matches/${event.id}` : opts.origin;
    lines.push(
      "BEGIN:VEVENT",
      `UID:event-${event.id}@${UID_DOMAIN}`,
      `DTSTAMP:${stamp}`,
      `DTSTART:${icsDate(start)}`,
      `DTEND:${icsDate(start + DEFAULT_DURATION_MS)}`,
      `SUMMARY:${icsEscape(eventTitle(event))}`,
      ...(event.venue ? [`LOCATION:${icsEscape(event.venue)}`] : []),
      `URL:${href}`,
      "END:VEVENT",
    );
  }
  lines.push("END:VCALENDAR");
  return lines.map(fold).join(CRLF) + CRLF;
}

/** A file name without characters calendars or browsers choke on. */
export function calendarFileName(name: string): string {
  const slug = name
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/ı/g, "i")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  return `${slug || "takvim"}-fikstur.ics`;
}
