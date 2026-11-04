import { api } from "@/lib/api";
import { finishedScore, RESULTS_BATCH } from "@/lib/predictions";

/**
 * Results for the prediction game: the browser sends the ids it holds predictions for, this
 * route asks our API (lib/api.ts) and answers with the finished ones only.
 */
export async function GET(request: Request): Promise<Response> {
  const ids = (new URL(request.url).searchParams.get("ids") ?? "")
    .split(",")
    .map(Number)
    .filter((n) => Number.isInteger(n) && n > 0)
    .slice(0, RESULTS_BATCH);
  const events = await Promise.all(ids.map((id) => api.event(id).catch(() => null)));
  const finished = events.flatMap((e) => {
    const score = e ? finishedScore(e) : null;
    return score ? [score] : [];
  });
  return Response.json({ finished });
}
