import type { MetadataRoute } from "next";
import { absoluteUrl } from "@/lib/site";

/** Personal, admin and sign-in pages are of no use in search results. */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/admin", "/me", "/signin", "/api/", "/offline"],
    },
    sitemap: absoluteUrl("/sitemap.xml"),
  };
}
