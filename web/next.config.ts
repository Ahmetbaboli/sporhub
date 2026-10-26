import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Docker image ships the minimal standalone server.
  output: "standalone",
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
