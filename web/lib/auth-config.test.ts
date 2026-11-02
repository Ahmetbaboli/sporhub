import { describe, expect, it } from "vitest";
import {
  devAccountId,
  enabledProviders,
  isAdminAccount,
  isAuthEnabled,
} from "@/lib/auth-config";
import { scoreMayBeDelayed } from "@/lib/sources";

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
    expect(
      enabledProviders({ ENABLE_DEV_LOGIN: "true", NODE_ENV: "development" }),
    ).toEqual(["dev"]);
    expect(
      enabledProviders({ ENABLE_DEV_LOGIN: "true", NODE_ENV: "production" }),
    ).toEqual([]);
  });
});

describe("isAuthEnabled", () => {
  const base = { ENABLE_DEV_LOGIN: "true", NODE_ENV: "development" };

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

describe("isAdminAccount", () => {
  it("is an explicit allow-list", () => {
    const env = { ADMIN_ACCOUNT_IDS: " github:1, google:2 " };
    expect(isAdminAccount("github:1", env)).toBe(true);
    expect(isAdminAccount("github:3", env)).toBe(false);
    expect(isAdminAccount("github:1", {})).toBe(false);
    expect(isAdminAccount("", { ADMIN_ACCOUNT_IDS: "" })).toBe(false);
  });
});

describe("scoreMayBeDelayed", () => {
  it("flags providers whose plan delays scores", () => {
    expect(scoreMayBeDelayed("football-data")).toBe(true);
    expect(scoreMayBeDelayed("jolpica")).toBe(false);
    expect(scoreMayBeDelayed(null)).toBe(false);
  });
});

describe("developer login", () => {
  it("needs both next dev and the explicit flag", () => {
    for (const NODE_ENV of ["production", "test", undefined]) {
      expect(enabledProviders({ ENABLE_DEV_LOGIN: "true", NODE_ENV })).not.toContain(
        "dev",
      );
    }
    expect(enabledProviders({ NODE_ENV: "development" })).not.toContain("dev");
    expect(enabledProviders({ ENABLE_DEV_LOGIN: "1", NODE_ENV: "development" })).toEqual(
      [],
    );
  });
});
