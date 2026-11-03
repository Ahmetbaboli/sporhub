import "server-only";
import { cookies } from "next/headers";
import { parseTribune, TRIBUNE_COOKIE, type Tribune } from "@/lib/tribune";

/** The visitor's on-device favourites (empty when the cookie is missing or malformed). */
export async function getTribune(): Promise<Tribune> {
  const store = await cookies();
  return parseTribune(store.get(TRIBUNE_COOKIE)?.value);
}
