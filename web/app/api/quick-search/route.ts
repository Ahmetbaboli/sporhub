import { ApiError, api } from "@/lib/api";
import { EMPTY_RESULTS, MIN_QUICK_QUERY } from "@/lib/quick-search";

const MAX_QUERY_LENGTH = 100;

/**
 * Same-origin bridge for the Ctrl+K search: the browser asks this route, the route asks our
 * API through lib/api.ts. No CORS setup and the API address stays server-side.
 */
export async function GET(request: Request): Promise<Response> {
  const q = (new URL(request.url).searchParams.get("q") ?? "")
    .trim()
    .slice(0, MAX_QUERY_LENGTH);
  if (q.length < MIN_QUICK_QUERY) return Response.json({ query: q, ...EMPTY_RESULTS });
  try {
    return Response.json(await api.search(q));
  } catch (error) {
    const status = error instanceof ApiError && error.status < 500 ? error.status : 502;
    return Response.json({ query: q, ...EMPTY_RESULTS }, { status });
  }
}
