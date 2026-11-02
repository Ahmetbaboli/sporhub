import "server-only";
import { auth } from "@/auth";
import { mintApiToken } from "@/lib/api-token";
import { isAuthEnabled } from "@/lib/auth-config";

export interface Viewer {
  name: string | null;
  image: string | null;
  /** A fresh short-lived bearer token for the Just Sport API. */
  token: () => Promise<string>;
}

export function authEnabled(): boolean {
  return isAuthEnabled(process.env);
}

/** The signed-in user, or null when signed out or when login is not configured. */
export async function getViewer(): Promise<Viewer | null> {
  if (!authEnabled()) return null;
  const session = await auth();
  const sub = session?.accountId;
  if (!session || !sub) return null;
  const name = session.user?.name ?? null;
  const image = session.user?.image ?? null;
  return {
    name,
    image,
    token: () =>
      mintApiToken({ sub, name, picture: image }, process.env.API_TOKEN_SECRET ?? ""),
  };
}
