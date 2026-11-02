// @vitest-environment node
import { describe, expect, it } from "vitest";
import { decodeProtectedHeader, jwtVerify } from "jose";
import {
  mintApiToken,
  TOKEN_AUDIENCE,
  TOKEN_ISSUER,
  TOKEN_LIFETIME_SECONDS,
} from "@/lib/api-token";

const SECRET = "s".repeat(48);
const key = new TextEncoder().encode(SECRET);

describe("mintApiToken", () => {
  it("matches the API contract (HS256, iss/aud/sub, short lifetime)", async () => {
    const now = new Date();
    const token = await mintApiToken(
      { sub: "github:42", name: "Ayşe", picture: null },
      SECRET,
      now,
    );
    expect(decodeProtectedHeader(token).alg).toBe("HS256");
    const { payload } = await jwtVerify(token, key, {
      issuer: TOKEN_ISSUER,
      audience: TOKEN_AUDIENCE,
    });
    expect(payload.sub).toBe("github:42");
    expect(payload.name).toBe("Ayşe");
    expect(payload).not.toHaveProperty("picture");
    expect(payload.exp! - payload.iat!).toBe(TOKEN_LIFETIME_SECONDS);
    expect(TOKEN_LIFETIME_SECONDS).toBeLessThanOrEqual(300);
  });

  it("cannot be verified with another secret", async () => {
    const token = await mintApiToken({ sub: "dev:x" }, SECRET);
    await expect(
      jwtVerify(token, new TextEncoder().encode("o".repeat(48))),
    ).rejects.toThrow();
  });
});
