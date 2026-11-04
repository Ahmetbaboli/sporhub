import { describe, expect, it } from "vitest";
import { buildCalendar, calendarFileName, icsDate, icsEscape } from "@/lib/ics";
import { event } from "@/tests/factories";

describe("ics", () => {
  it("writes one VEVENT per match with UTC times and a link back", () => {
    const ics = buildCalendar(
      [event({ id: 44, status: "scheduled", venue: "RAMS Park, İstanbul" })],
      { name: "Galatasaray · Just Sport", origin: "https://js.test", now: 0 },
    );
    expect(ics.startsWith("BEGIN:VCALENDAR\r\n")).toBe(true);
    expect(ics.endsWith("END:VCALENDAR\r\n")).toBe(true);
    expect(ics).toContain("UID:event-44@justsport");
    expect(ics).toContain("DTSTART:20261026T173000Z");
    expect(ics).toContain("DTEND:20261026T193000Z");
    expect(ics).toContain("SUMMARY:Arsenal FC – Chelsea FC (Premier League)");
    expect(ics).toContain(String.raw`LOCATION:RAMS Park\, İstanbul`);
    expect(ics).toContain("URL:https://js.test/matches/44");
    expect(ics).not.toMatch(/[^\r]\n/); // CRLF only
  });

  it("folds long lines and escapes special characters", () => {
    const long = buildCalendar([], { name: "x".repeat(200), origin: "o", now: 0 });
    expect(long.split("\r\n").every((l) => [...l].length <= 75)).toBe(true);
    expect(icsEscape("a;b,c\nd\\")).toBe(String.raw`a\;b\,c\nd\\`);
    expect(icsDate(Date.UTC(2026, 10, 4, 9, 5, 0))).toBe("20261104T090500Z");
  });

  it("makes a plain file name", () => {
    expect(calendarFileName("Beşiktaş")).toBe("besiktas-fikstur.ics");
    expect(calendarFileName("İstanbul Başakşehir")).toBe(
      "istanbul-basaksehir-fikstur.ics",
    );
  });
});
