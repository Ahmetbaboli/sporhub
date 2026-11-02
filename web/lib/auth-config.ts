/**
 * Which sign-in options are switched on, decided from the environment alone so the rest of the
 * app can ask "is login available?" without touching Auth.js. Missing configuration means the
 * site simply runs signed-out (no errors, no login button).
 */
export type ProviderId = "github" | "google" | "dev";

export interface AuthEnv {
  AUTH_SECRET?: string;
  API_TOKEN_SECRET?: string;
  AUTH_GITHUB_ID?: string;
  AUTH_GITHUB_SECRET?: string;
  AUTH_GOOGLE_ID?: string;
  AUTH_GOOGLE_SECRET?: string;
  AUTH_DEV_LOGIN?: string;
  NODE_ENV?: string;
}

export const MIN_API_SECRET_LENGTH = 32;

export function enabledProviders(env: AuthEnv): ProviderId[] {
  const providers: ProviderId[] = [];
  if (env.AUTH_GITHUB_ID && env.AUTH_GITHUB_SECRET) providers.push("github");
  if (env.AUTH_GOOGLE_ID && env.AUTH_GOOGLE_SECRET) providers.push("google");
  // Name-only login for local demos; never available in a production build.
  if (env.AUTH_DEV_LOGIN === "true" && env.NODE_ENV !== "production") {
    providers.push("dev");
  }
  return providers;
}

export function isAuthEnabled(env: AuthEnv): boolean {
  return (
    Boolean(env.AUTH_SECRET) &&
    (env.API_TOKEN_SECRET?.length ?? 0) >= MIN_API_SECRET_LENGTH &&
    enabledProviders(env).length > 0
  );
}

/** "Ayşe Yılmaz" -> "ayse-yilmaz": stable account id for the dev provider. */
export function devAccountId(name: string): string {
  return name
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/ı/g, "i")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}
