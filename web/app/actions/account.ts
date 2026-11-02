"use server";

import { revalidatePath } from "next/cache";
import { signIn, signOut } from "@/auth";
import { api } from "@/lib/api";
import { getViewer } from "@/lib/session";
import type { FavoriteKind } from "@/lib/types";

const FAVORITE_KINDS: readonly FavoriteKind[] = ["teams", "players", "competitions"];

export type FavoriteResult =
  { ok: true } | { ok: false; reason: "signed_out" | "failed" };

/** Follows or unfollows one entity for the signed-in user (idempotent on the API side). */
export async function setFavorite(
  kind: FavoriteKind,
  id: number,
  follow: boolean,
): Promise<FavoriteResult> {
  if (!FAVORITE_KINDS.includes(kind) || !Number.isInteger(id) || id < 1) {
    return { ok: false, reason: "failed" };
  }
  const viewer = await getViewer();
  if (!viewer) return { ok: false, reason: "signed_out" };
  try {
    const token = await viewer.token();
    await (follow ? api.me.addFavorite : api.me.removeFavorite)(token, kind, id);
  } catch {
    return { ok: false, reason: "failed" };
  }
  revalidatePath("/me");
  revalidatePath("/");
  return { ok: true };
}

export async function signInWith(provider: string, formData: FormData): Promise<void> {
  const callbackUrl = safeCallback(formData.get("callbackUrl"));
  const options: Record<string, unknown> = { redirectTo: callbackUrl };
  if (provider === "dev") options.name = formData.get("name");
  await signIn(provider, options);
}

export async function signOutAction(): Promise<void> {
  await signOut({ redirectTo: "/" });
}

/** Only same-site relative paths are allowed as post-login destinations. */
function safeCallback(value: FormDataEntryValue | null): string {
  return typeof value === "string" && value.startsWith("/") && !value.startsWith("//")
    ? value
    : "/me";
}
