import { describe, expect, it } from "vitest";
import { devAccountId, enabledProviders, isAuthEnabled } from "@/lib/auth-config";

const SECRET = "x".repeat(32);

describe("enabledProviders", () => {
  it("needs both id and secret for OAuth providers", () => {
    expect(enabledProviders({ AUTH_GITHUB_ID: "a" })).toEqual([]);
    expect(
      enabledProviders({
        AUTH_GITHUB_ID: "a",
        AUTH_GITHUB_SECRET: "b",
        AUTH_GOOGLE_ID: "c",
        AUTH_GOOGLE_SECRET: "d",
      }),
    ).toEqual(["github", "google"]);
  });

  it("never enables the dev login in production", () => {
    expect(enabledProviders({ AUTH_DEV_LOGIN: "true", NODE_ENV: "development" })).toEqual(
      ["dev"],
    );
    expect(enabledProviders({ AUTH_DEV_LOGIN: "true", NODE_ENV: "production" })).toEqual(
      [],
    );
  });
});

describe("isAuthEnabled", () => {
  const base = { AUTH_DEV_LOGIN: "true", NODE_ENV: "test" };

  it("requires the session secret, a long API secret and a provider", () => {
    expect(isAuthEnabled({ ...base, AUTH_SECRET: "s", API_TOKEN_SECRET: SECRET })).toBe(
      true,
    );
    expect(isAuthEnabled({ ...base, API_TOKEN_SECRET: SECRET })).toBe(false);
    expect(isAuthEnabled({ ...base, AUTH_SECRET: "s", API_TOKEN_SECRET: "short" })).toBe(
      false,
    );
    expect(isAuthEnabled({ AUTH_SECRET: "s", API_TOKEN_SECRET: SECRET })).toBe(false);
  });
});

describe("devAccountId", () => {
  it("slugifies Turkish names", () => {
    expect(devAccountId("  Ayşe Işık Öztürk ")).toBe("ayse-isik-ozturk");
    expect(devAccountId("!!!")).toBe("");
  });
});
