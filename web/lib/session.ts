import "server-only";
import { auth } from "@/auth";
import { mintApiToken } from "@/lib/api-token";
import { isAdminAccount, isAuthEnabled } from "@/lib/auth-config";

export interface Viewer {
  /** "<provider>:<account id>", e.g. "github:12345". */
  accountId: string;
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
    accountId: sub,
    name,
    image,
    token: () =>
      mintApiToken({ sub, name, picture: image }, process.env.API_TOKEN_SECRET ?? ""),
  };
}

/** Comma-separated ADMIN_ACCOUNT_IDS (e.g. "github:12345") may open admin pages. */
export function isAdmin(viewer: Viewer | null): boolean {
  return (
    viewer !== null &&
    isAdminAccount(viewer.accountId, { ADMIN_ACCOUNT_IDS: process.env.ADMIN_ACCOUNT_IDS })
  );
}
