import type { Metadata } from "next";
import { initLocale, t } from "@/lib/i18n";

export async function generateMetadata(): Promise<Metadata> {
  await initLocale();
  return { title: t().privacy.title };
}

export default async function PrivacyPage() {
  await initLocale();
  const p = t().privacy;
  const section = "font-display text-primary mt-8 mb-2 text-2xl font-semibold uppercase";
  return (
    <article className="mx-auto max-w-2xl leading-relaxed">
      <h1 className="font-display text-4xl font-bold tracking-tight uppercase">
        {p.title}
      </h1>
      <p className="mt-4">{p.intro}</p>
      <h2 className={section}>{p.storedTitle}</h2>
      <ul className="list-disc space-y-1 pl-5">
        {p.stored.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
      <h2 className={section}>{p.cookiesTitle}</h2>
      <ul className="list-disc space-y-1 pl-5">
        {p.cookies.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
      <h2 className={section}>{p.notTitle}</h2>
      <p>{p.not}</p>
      <h2 className={section}>{p.deleteTitle}</h2>
      <p>{p.delete}</p>
      <h2 className={section}>{p.contactTitle}</h2>
      <p>{p.contact}</p>
      <p className="text-muted-foreground mt-8 text-xs">{p.updated}</p>
    </article>
  );
}
