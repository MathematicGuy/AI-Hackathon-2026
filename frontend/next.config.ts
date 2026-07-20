import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: "standalone",
  // Development only: `next dev` serves the app on :3000 without nginx in
  // front, so proxy /api/* to the backend. In production nginx routes /api/
  // straight to the backend and these rewrites are never consulted.
  // BACKEND_ORIGIN is server-side only and never reaches the client bundle.
  async rewrites() {
    if (process.env.NODE_ENV === "production") {
      return [];
    }

    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_ORIGIN ?? "http://127.0.0.1:8000"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
