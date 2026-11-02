import { describe, expect, it } from "vitest";
import { checkWebEnv } from "@/lib/env-check";

const SECRET = "x".repeat(40);

describe("checkWebEnv", () => {
  it("accepts a signed-out production site with an API URL", () => {
    expect(
      checkWebEnv({ NODE_ENV: "production", NEXT_PUBLIC_API_URL: "https://api.test" }),
    ).toEqual({ errors: [], warnings: [] });
  });

  it("names missing or half-configured variables without echoing values", () => {
    const { errors } = checkWebEnv({
      NODE_ENV: "production",
      AUTH_GITHUB_ID: "id-value",
      API_TOKEN_SECRET: "short",
    });
    expect(errors.join("\n")).toMatch(/NEXT_PUBLIC_API_URL/);
    expect(errors.join("\n")).toMatch(/AUTH_GITHUB_SECRET/);
    expect(errors.join("\n")).not.toMatch(/id-value|short/);
  });

  it("requires the session and API secrets once a provider is configured", () => {
    const base = {
      NEXT_PUBLIC_API_URL: "https://api.test",
      AUTH_GITHUB_ID: "a",
      AUTH_GITHUB_SECRET: "b",
    };
    expect(checkWebEnv(base).errors).toHaveLength(2);
    expect(
      checkWebEnv({ ...base, AUTH_SECRET: "s", API_TOKEN_SECRET: SECRET }).errors,
    ).toEqual([]);
  });
});
