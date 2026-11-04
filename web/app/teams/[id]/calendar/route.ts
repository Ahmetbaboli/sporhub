import { ApiError, api } from "@/lib/api";
import { buildCalendar, calendarFileName } from "@/lib/ics";

const EVENTS_FETCH_SIZE = 100;

/** The team's upcoming fixtures as an .ics file (opens in any calendar app). */
export async function GET(
  request: Request,
  ctx: { params: Promise<{ id: string }> },
): Promise<Response> {
  const id = Number((await ctx.params).id);
  if (!Number.isInteger(id) || id <= 0) return new Response("Not found", { status: 404 });
  try {
    const [team, events] = await Promise.all([
      api.team(id),
      api.teamEvents(id, { order: "desc", pageSize: EVENTS_FETCH_SIZE }),
    ]);
    const now = Date.now();
    const upcoming = events.items
      .filter((e) => e.status === "scheduled" && Date.parse(e.start_time) > now)
      .sort((a, b) => a.start_time.localeCompare(b.start_time));
    const body = buildCalendar(upcoming, {
      name: `${team.name} · Just Sport`,
      origin: new URL(request.url).origin,
      now,
    });
    return new Response(body, {
      headers: {
        "Content-Type": "text/calendar; charset=utf-8",
        "Content-Disposition": `attachment; filename="${calendarFileName(team.name)}"`,
        "Cache-Control": "public, max-age=900",
      },
    });
  } catch (error) {
    const status = error instanceof ApiError && error.status === 404 ? 404 : 502;
    return new Response(status === 404 ? "Not found" : "Unavailable", { status });
  }
}
