import type { NextConfig } from "next";

// In the cluster the gateway routes /api/* to services before requests reach Next.js.
// With `pnpm dev` on the host, forward /api/* to the gateway so the same relative URLs work.
const gateway = process.env.SDL_GATEWAY_URL ?? "http://localhost:8080";

const config: NextConfig = {
  output: "standalone",
  async rewrites() {
    if (process.env.NODE_ENV !== "development") return [];
    return [{ source: "/api/:path*", destination: `${gateway}/api/:path*` }];
  },
};

export default config;
