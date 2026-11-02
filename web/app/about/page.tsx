import type { Metadata } from "next";
import Link from "next/link";
import { initLocale, t } from "@/lib/i18n";

export async function generateMetadata(): Promise<Metadata> {
  await initLocale();
  return { title: t().about.title };
}

export default async function AboutPage() {
  await initLocale();
  const a = t().about;
  return (
    <article className="mx-auto max-w-2xl space-y-4 leading-relaxed">
      <h1 className="font-display text-4xl font-bold tracking-tight uppercase">
        {a.title}
      </h1>
      {a.body.map((paragraph) => (
        <p key={paragraph}>{paragraph}</p>
      ))}
      <p className="flex gap-4 text-sm">
        <Link href="/sources" className="text-primary underline">
          {a.sourcesLink}
        </Link>
        <Link href="/privacy" className="text-primary underline">
          {a.privacyLink}
        </Link>
      </p>
    </article>
  );
}
