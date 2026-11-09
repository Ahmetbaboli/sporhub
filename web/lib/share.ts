import type { Metadata } from "next";
import { t } from "@/lib/i18n";

/**
 * Title + description for a page and its share card. A page's `openGraph` replaces the
 * layout's, so the common fields are repeated here; the picture itself comes from the
 * route's opengraph-image file.
 */
export function shareMetadata(title: string, description: string): Metadata {
  const { app } = t();
  return {
    title,
    description,
    openGraph: {
      title: `${title} · ${app.name}`,
      description,
      siteName: app.name,
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title: `${title} · ${app.name}`,
      description,
    },
  };
}
