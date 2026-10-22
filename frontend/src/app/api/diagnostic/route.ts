import { NextResponse } from "next/server";
import { getResolvedBackendConfig, maskUrlForLogs } from "@/lib/serverConfig";

export const dynamic = "force-dynamic";

export async function GET() {
  const isProduction = process.env.NODE_ENV === "production";
  const backendConfig = getResolvedBackendConfig();

  let reachable = false;
  let httpStatus: number | null = null;
  let latencyMs: number | null = null;
  let probeError: string | null = null;
  let healthPayload: any = null;

  if (backendConfig.isValid) {
    const healthUrl = `${backendConfig.normalizedUrl}/health`;
    const start = Date.now();
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s probe timeout

      const res = await fetch(healthUrl, {
        method: "GET",
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      latencyMs = Date.now() - start;
      httpStatus = res.status;
      if (res.ok) {
        reachable = true;
        healthPayload = await res.json().catch(() => null);
      } else {
        probeError = `Backend returned HTTP ${res.status}`;
      }
    } catch (err: any) {
      latencyMs = Date.now() - start;
      probeError =
        err?.name === "AbortError"
          ? "Probe connection timed out (5s)"
          : err?.message || "Connection refused";
    }
  } else {
    probeError = backendConfig.errorMessage || "Backend not configured";
  }

  const geminiKey = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY || "";
  const geminiConfigured = Boolean(
    geminiKey && !geminiKey.includes("CHANGE_ME") && !geminiKey.includes("YOUR_")
  );

  let systemStatus: "OPERATIONAL" | "DEGRADED" | "UNCONFIGURED" | "PLACEHOLDER_ERROR" | "BACKEND_UNREACHABLE";
  if (backendConfig.isValid && reachable) {
    systemStatus = "OPERATIONAL";
  } else if (!backendConfig.isValid && backendConfig.errorType === "PLACEHOLDER") {
    systemStatus = "PLACEHOLDER_ERROR";
  } else if (!backendConfig.isValid) {
    systemStatus = "UNCONFIGURED";
  } else {
    systemStatus = "BACKEND_UNREACHABLE";
  }

  return NextResponse.json({
    system: "TRUST-ID / Nyaya-Tula AI",
    status: systemStatus,
    timestamp: new Date().toISOString(),
    environment: isProduction ? "production" : "development",
    backend_configuration: {
      configured: backendConfig.isValid,
      variable_source: backendConfig.variableUsed,
      target_url_masked: maskUrlForLogs(backendConfig.normalizedUrl || backendConfig.rawUrl),
      error_type: backendConfig.errorType || null,
      error_message: backendConfig.errorMessage || null,
      user_action: backendConfig.userAction || null,
    },
    connectivity: {
      reachable,
      http_status: httpStatus,
      latency_ms: latencyMs,
      checked_endpoint: backendConfig.isValid ? `${maskUrlForLogs(backendConfig.normalizedUrl)}/health` : null,
      error: probeError,
      health_details: healthPayload,
    },
    multimodal_vision_fallback: {
      gemini_configured: geminiConfigured,
      model: process.env.GEMINI_MODEL || "gemini-2.5-flash",
    },
    vercel_environment_guide: {
      primary_variable: "BACKEND_API_URL",
      primary_description: "Server-side FastAPI backend base URL (e.g. https://your-service.onrender.com).",
      primary_visibility: "Sensitive / Secret (Server-side only; never leaked to client bundles)",
      optional_variable: "NEXT_PUBLIC_API_URL",
      optional_description: "Optional browser-side override. Not needed if using Next.js /api/backend reverse proxy.",
      optional_visibility_rule: "MUST use 'Plaintext / Config' in Vercel. Vercel rejects 'Secret' visibility on NEXT_PUBLIC_* variables.",
    },
  });
}
