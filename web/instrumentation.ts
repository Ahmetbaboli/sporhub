import { checkWebEnv } from "@/lib/env-check";

/** Runs once when the Next.js server starts. */
export function register(): void {
  if (process.env.NEXT_RUNTIME !== "nodejs") return;
  const { errors, warnings } = checkWebEnv(process.env);
  for (const warning of warnings) console.warn(`[config] ${warning}`);
  if (errors.length === 0) return;
  const message = `Yapılandırma hatası:\n${errors.map((e) => `  - ${e}`).join("\n")}`;
  if (process.env.NODE_ENV === "production") throw new Error(message);
  console.error(message);
}
