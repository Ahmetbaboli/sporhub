import { describe, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/api";
import { orNotFound, parseId, parsePage } from "@/lib/api-helpers";

// next/navigation's notFound() throws a special error; model it so we can assert on it.
class NotFoundSignal extends Error {}
vi.mock("next/navigation", () => ({
  notFound: () => {
    throw new NotFoundSignal("NEXT_NOT_FOUND");
  },
}));

describe("orNotFound", () => {
  it("passes the value through", async () => {
    await expect(orNotFound(Promise.resolve(42))).resolves.toBe(42);
  });

  it("turns an API 404 into notFound()", async () => {
    const request = Promise.reject(new ApiError(404, "not_found", "yok"));
    await expect(orNotFound(request)).rejects.toBeInstanceOf(NotFoundSignal);
  });

  it("lets other API errors reach the error boundary", async () => {
    const request = Promise.reject(new ApiError(503, "unreachable", "down"));
    await expect(orNotFound(request)).rejects.toMatchObject({ status: 503 });
  });
});

describe("route params", () => {
  it("parseId accepts digits only", () => {
    expect(parseId("12")).toBe(12);
    expect(() => parseId("abc")).toThrow(NotFoundSignal);
    expect(() => parseId("1; drop")).toThrow(NotFoundSignal);
  });

  it("parsePage falls back to 1", () => {
    expect(parsePage("3")).toBe(3);
    expect(parsePage("0")).toBe(1);
    expect(parsePage(undefined)).toBe(1);
    expect(parsePage(["2", "5"])).toBe(2);
  });
});
