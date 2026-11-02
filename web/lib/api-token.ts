/**
 * Short-lived HS256 tokens the web server signs for the API on behalf of a signed-in user.
 * The contract is pinned in api/app/core/auth.py (iss, aud, sub = "<provider>:<id>",
 * exp - iat <= 300 s). Never import this from client components: it needs the shared secret.
 */
import { SignJWT } from "jose";

export const TOKEN_ISSUER = "justsport-web";
export const TOKEN_AUDIENCE = "justsport-api";
export const TOKEN_LIFETIME_SECONDS = 120;

export interface TokenSubject {
  sub: string;
  name?: string | null;
  picture?: string | null;
}

export async function mintApiToken(
  subject: TokenSubject,
  secret: string,
  now: Date = new Date(),
): Promise<string> {
  const iat = Math.floor(now.getTime() / 1000);
  const claims: Record<string, string> = {};
  if (subject.name) claims.name = subject.name;
  if (subject.picture) claims.picture = subject.picture;
  return new SignJWT(claims)
    .setProtectedHeader({ alg: "HS256" })
    .setIssuer(TOKEN_ISSUER)
    .setAudience(TOKEN_AUDIENCE)
    .setSubject(subject.sub)
    .setIssuedAt(iat)
    .setExpirationTime(iat + TOKEN_LIFETIME_SECONDS)
    .sign(new TextEncoder().encode(secret));
}
