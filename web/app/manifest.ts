import type { MetadataRoute } from "next";

/** Lets phones install the site like an app ("Add to Home screen"). */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Just Sport",
    short_name: "Just Sport",
    description:
      "Futbol, basketbol ve Formula 1: canlı skor, fikstür, puan durumu ve haber.",
    lang: "tr",
    start_url: "/",
    scope: "/",
    display: "standalone",
    background_color: "#0b1018",
    theme_color: "#0b1018",
    icons: [
      { src: "/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
    shortcuts: [
      { name: "Bugün", url: "/" },
      { name: "Skor Tahmini", url: "/tahmin" },
      { name: "Benim Tribünüm", url: "/tribun" },
    ],
  };
}
