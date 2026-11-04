import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Docker image ships the minimal standalone server.
  output: "standalone",
  // The service worker must never be served stale, or fixes to it would not reach phones.
  async headers() {
    return [
      {
        source: "/sw.js",
        headers: [
          { key: "Content-Type", value: "application/javascript; charset=utf-8" },
          { key: "Cache-Control", value: "no-cache, no-store, must-revalidate" },
        ],
      },
    ];
  },
  // Club crests come from many hosts; they are rendered with plain <img> + fallback.
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
