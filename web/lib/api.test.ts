import { afterEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, buildUrl } from "@/lib/api";

afterEach(() => vi.restoreAllMocks());

const jsonResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

describe("buildUrl", () => {
  it("skips empty values and repeats array params", () => {
    const url = new URL(
      buildUrl("/api/v1/x", {
        status: ["live", "scheduled"],
        page: 2,
        q: undefined,
        a: "",
      }),
    );
    expect(url.pathname).toBe("/api/v1/x");
    expect(url.searchParams.getAll("status")).toEqual(["live", "scheduled"]);
    expect(url.searchParams.get("page")).toBe("2");
    expect(url.searchParams.has("q")).toBe(false);
    expect(url.searchParams.has("a")).toBe(false);
  });
});

describe("api client", () => {
  it("sends the default time zone for today's events", async () => {
    const spy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ items: [], total: 0, page: 1, page_size: 1 }));
    await api.todayEvents({ sport: "football" });
    const url = new URL(String(spy.mock.calls[0][0]));
    expect(url.pathname).toBe("/api/v1/events/today");
    expect(url.searchParams.get("tz")).toBe("Europe/Istanbul");
    expect(url.searchParams.get("sport")).toBe("football");
  });

  it("maps competition events options to API parameter names", async () => {
    const spy = vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse({}));
    await api.competitionEvents("premier-league", {
      pageSize: 5,
      order: "desc",
      status: ["finished"],
    });
    const url = new URL(String(spy.mock.calls[0][0]));
    expect(url.searchParams.get("page_size")).toBe("5");
    expect(url.searchParams.get("status")).toBe("finished");
  });

  it("turns the API error envelope into ApiError", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ error: { code: "not_found", message: "Takım bulunamadı." } }, 404),
    );
    await expect(api.team(1)).rejects.toMatchObject({
      status: 404,
      code: "not_found",
      message: "Takım bulunamadı.",
    });
  });

  it("wraps network failures as an unreachable ApiError", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("fetch failed"));
    const error = await api.sports().catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).code).toBe("unreachable");
  });
});
