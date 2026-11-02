import { FlaskConical } from "lucide-react";
import { api } from "@/lib/api";
import { t } from "@/lib/i18n";

/** Shown on every page when the API runs with DATA_MODE=demo. */
export async function DemoBanner() {
  const meta = await api.meta().catch(() => null);
  if (meta?.data_mode !== "demo") return null;
  return (
    <div
      role="note"
      className="bg-accent text-accent-foreground flex items-center justify-center gap-2 px-4 py-1.5 text-center text-xs font-semibold"
    >
      <FlaskConical className="size-4 shrink-0" aria-hidden />
      <span className="uppercase">{t().demo.banner}</span>
      <span className="font-normal">{t().demo.bannerBody}</span>
    </div>
  );
}
