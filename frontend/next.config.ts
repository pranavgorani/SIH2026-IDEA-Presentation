import type { NextConfig } from "next";

const isDev = process.env.NODE_ENV !== "production";
const rawBackendUrl =
  process.env.BACKEND_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  (isDev ? "http://127.0.0.1:8000" : "");

const backendUrl = rawBackendUrl.replace(/\/$/, "");

const nextConfig: NextConfig = {
  async rewrites() {
    if (!backendUrl) {
      return [];
    }
    return [
      {
        source: "/api/backend/:path*",
        destination: `${backendUrl}/api/backend/:path*`,
      },
      {
        source: "/health",
        destination: `${backendUrl}/health`,
      },
      {
        source: "/docs",
        destination: `${backendUrl}/docs`,
      },
    ];
  },
};

export default nextConfig;
