import type { NextConfig } from "next";

const backendUrl = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: `${backendUrl.replace(/\/$/, "")}/api/backend/:path*`,
      },
      {
        source: "/api/:path*",
        destination: `${backendUrl.replace(/\/$/, "")}/api/:path*`,
      },
      {
        source: "/health",
        destination: `${backendUrl.replace(/\/$/, "")}/health`,
      },
      {
        source: "/docs",
        destination: `${backendUrl.replace(/\/$/, "")}/docs`,
      },
    ];
  },
};

export default nextConfig;
