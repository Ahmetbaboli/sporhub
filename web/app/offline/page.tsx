import { WifiOff } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { initLocale, t } from "@/lib/i18n";

export async function generateMetadata(): Promise<Metadata> {
  await initLocale();
  return { title: t().offline.title, robots: { index: false } };
}

/** Shown by the service worker when a page cannot be loaded without a connection. */
export default async function OfflinePage() {
  await initLocale();
  return (
    <div className="mx-auto flex max-w-md flex-col items-center py-16 text-center">
      <WifiOff className="text-muted-foreground size-12" aria-hidden />
      <h1 className="font-display mt-4 text-3xl font-bold uppercase">
        {t().offline.title}
      </h1>
      <p className="text-muted-foreground mt-2 text-sm">{t().offline.body}</p>
      <Link
        href="/"
        className="bg-primary text-primary-foreground mt-6 inline-flex h-10 items-center rounded-md px-4 text-sm font-semibold"
      >
        {t().offline.retry}
      </Link>
    </div>
  );
}
