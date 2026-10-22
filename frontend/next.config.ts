import type { NextConfig } from "next";
import { getResolvedBackendConfig, maskUrlForLogs } from "./src/lib/serverConfig";

const backendConfig = getResolvedBackendConfig();
const backendUrl = backendConfig.isValid ? backendConfig.normalizedUrl : "";

if (!backendConfig.isValid && process.env.NODE_ENV === "production") {
  console.warn(
    `[TRUST-ID Gateway Notice] Production backend is not yet connected: ${backendConfig.errorMessage || "BACKEND_API_URL missing"}. ` +
      `Server-side rewrites will activate once BACKEND_API_URL is set in Vercel.`
  );
} else if (backendConfig.isValid) {
  console.log(
    `[TRUST-ID Gateway] Active backend target (${backendConfig.variableUsed}): ${maskUrlForLogs(backendUrl)}`
  );
}

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
