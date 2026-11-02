/**
 * Start-up configuration check for the web server (instrumentation.ts). Names variables, never
 * prints values. Errors stop a production server; in development they are logged.
 */
import { MIN_API_SECRET_LENGTH } from "@/lib/auth-config";

type Env = Record<string, string | undefined>;

const PAIRS: [string, string][] = [
  ["AUTH_GITHUB_ID", "AUTH_GITHUB_SECRET"],
  ["AUTH_GOOGLE_ID", "AUTH_GOOGLE_SECRET"],
];

export function checkWebEnv(env: Env): { errors: string[]; warnings: string[] } {
  const errors: string[] = [];
  const warnings: string[] = [];
  const production = env.NODE_ENV === "production";
  if (production && !env.NEXT_PUBLIC_API_URL) {
    errors.push("NEXT_PUBLIC_API_URL tanımlı değil: site API'ye ulaşamaz.");
  }
  for (const [id, secret] of PAIRS) {
    if (Boolean(env[id]) !== Boolean(env[secret])) {
      errors.push(`${id} ve ${secret} birlikte tanımlanmalı.`);
    }
  }
  const anyProvider = PAIRS.some(([id, secret]) => env[id] && env[secret]);
  if (anyProvider && !env.AUTH_SECRET) {
    errors.push("Giriş sağlayıcısı var ama AUTH_SECRET tanımlı değil.");
  }
  if (anyProvider && (env.API_TOKEN_SECRET?.length ?? 0) < MIN_API_SECRET_LENGTH) {
    errors.push(
      `API_TOKEN_SECRET en az ${MIN_API_SECRET_LENGTH} karakter olmalı (API ile aynı değer).`,
    );
  }
  if (env.ADMIN_ACCOUNT_IDS && !env.ADMIN_TOKEN) {
    warnings.push(
      "ADMIN_ACCOUNT_IDS var ama ADMIN_TOKEN yok: /admin/status veri gösteremez.",
    );
  }
  if (production && env.ENABLE_DEV_LOGIN === "true") {
    warnings.push("ENABLE_DEV_LOGIN üretim derlemesinde yok sayılır.");
  }
  return { errors, warnings };
}
