/**
 * TRUST-ID / Nyaya-Tula AI — Server-Side Backend Configuration & URL Validator
 *
 * Rules:
 * 1. BACKEND_API_URL is the authoritative server-side environment variable.
 *    It is never exposed in browser bundles and can have Secret / Sensitive visibility in Vercel.
 * 2. Never attempt to query placeholder URLs (e.g. strings with <>, CHANGE_ME, YOUR_*, PLACEHOLDER).
 * 3. In production, localhost / 127.0.0.1 is rejected as an unreachable local endpoint.
 * 4. Error code for invalid configuration is strictly BACKEND_CONFIGURATION_ERROR.
 */

export interface BackendValidationResult {
  isValid: boolean;
  rawUrl: string;
  normalizedUrl: string;
  isPlaceholder: boolean;
  errorType?: "MISSING" | "PLACEHOLDER" | "LOCALHOST_IN_PRODUCTION" | "UNRESOLVED_DOCKER_HOST" | "INVALID_PROTOCOL" | "MALFORMED";
  errorMessage?: string;
  userAction?: string;
  variableUsed: "BACKEND_API_URL" | "NEXT_PUBLIC_API_URL" | "DEV_FALLBACK" | "NONE";
}

const PLACEHOLDER_PATTERNS = [
  /<[^>]+>/, // e.g. <your-backend-name> or <your-render-url>
  /CHANGE_ME/i,
  /YOUR_/i,
  /PLACEHOLDER/i,
  /MY_BACKEND/i,
  /EXAMPLE\.COM/i,
  /EXAMPLE\.ORG/i,
  /YOUR-SERVICE/i,
  /YOUR-APP/i,
  /YOUR-BACKEND/i,
  /\.\.\./,
];

export function isPlaceholderValue(val?: string | null): boolean {
  if (!val || typeof val !== "string") return true;
  const trimmed = val.trim();
  if (trimmed === "" || trimmed === "undefined" || trimmed === "null") return true;
  return PLACEHOLDER_PATTERNS.some((pattern) => pattern.test(trimmed));
}

export function validateBackendUrl(
  inputUrl?: string | null,
  isProduction: boolean = process.env.NODE_ENV === "production"
): BackendValidationResult {
  const raw = (inputUrl || "").trim();

  if (!raw) {
    return {
      isValid: false,
      rawUrl: "",
      normalizedUrl: "",
      isPlaceholder: false,
      errorType: "MISSING",
      errorMessage: "Backend screening engine is not configured (missing BACKEND_API_URL).",
      userAction: isProduction
        ? "If your backend is deployed as a separate Vercel project, retrieve its domain from the Vercel Dashboard (Project → Overview → Domains) and add BACKEND_API_URL in this project's Environment Variables."
        : "Set BACKEND_API_URL=http://127.0.0.1:8000 in your local .env or start the FastAPI server on port 8000.",
      variableUsed: "NONE",
    };
  }

  if (isPlaceholderValue(raw)) {
    return {
      isValid: false,
      rawUrl: raw,
      normalizedUrl: "",
      isPlaceholder: true,
      errorType: "PLACEHOLDER",
      errorMessage: `Supplied backend URL "${raw}" is an unreplaced template placeholder and cannot be used.`,
      userAction: "If your backend is deployed as a separate Vercel project, retrieve its real assigned domain from Vercel Dashboard (Project → Overview → Domains) and update BACKEND_API_URL.",
      variableUsed: "NONE",
    };
  }

  // Parse URL
  let parsed: URL;
  try {
    parsed = new URL(raw);
  } catch {
    return {
      isValid: false,
      rawUrl: raw,
      normalizedUrl: "",
      isPlaceholder: false,
      errorType: "MALFORMED",
      errorMessage: `Backend URL "${raw}" is not a valid absolute URL format.`,
      userAction: "Ensure the URL starts with https:// followed by your real assigned project hostname.",
      variableUsed: "NONE",
    };
  }

  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    return {
      isValid: false,
      rawUrl: raw,
      normalizedUrl: "",
      isPlaceholder: false,
      errorType: "INVALID_PROTOCOL",
      errorMessage: `Backend URL scheme "${parsed.protocol}" is unsupported. Only http: and https: are allowed.`,
      userAction: "Specify https:// for production or http:// for local development.",
      variableUsed: "NONE",
    };
  }

  const hostname = parsed.hostname.toLowerCase();

  // Localhost checks in production
  if (
    isProduction &&
    (hostname === "localhost" ||
      hostname === "127.0.0.1" ||
      hostname === "0.0.0.0" ||
      hostname === "::1")
  ) {
    return {
      isValid: false,
      rawUrl: raw,
      normalizedUrl: "",
      isPlaceholder: true,
      errorType: "LOCALHOST_IN_PRODUCTION",
      errorMessage: `Backend URL points to local address "${hostname}", which cannot be reached from Vercel in production.`,
      userAction: "Deploy your backend to Vercel (or cloud provider), retrieve the public assigned domain from its dashboard, and set BACKEND_API_URL.",
      variableUsed: "NONE",
    };
  }

  // Docker internal hostname check
  if (
    hostname === "backend" &&
    process.env.DOCKER_ENV !== "true" &&
    process.env.IS_DOCKER !== "true"
  ) {
    return {
      isValid: false,
      rawUrl: raw,
      normalizedUrl: "",
      isPlaceholder: true,
      errorType: "UNRESOLVED_DOCKER_HOST",
      errorMessage: `Backend hostname "backend" is an internal Docker Compose service name and cannot be resolved on Vercel.`,
      userAction: isProduction
        ? "Set BACKEND_API_URL to your public backend domain in Vercel."
        : "Set BACKEND_API_URL=http://127.0.0.1:8000 for local development.",
      variableUsed: "NONE",
    };
  }

  // Clean trailing slashes
  const normalized = `${parsed.protocol}//${parsed.host}${parsed.pathname === "/" ? "" : parsed.pathname}`.replace(/\/$/, "");

  return {
    isValid: true,
    rawUrl: raw,
    normalizedUrl: normalized,
    isPlaceholder: false,
    errorMessage: undefined,
    userAction: undefined,
    variableUsed: "NONE",
  };
}

export function getResolvedBackendConfig(): BackendValidationResult {
  const isProduction = process.env.NODE_ENV === "production";
  const backendApiUrl = process.env.BACKEND_API_URL;
  const nextPublicApiUrl = process.env.NEXT_PUBLIC_API_URL;

  // 1. Check BACKEND_API_URL (primary server-side variable)
  if (backendApiUrl && !isPlaceholderValue(backendApiUrl)) {
    const res = validateBackendUrl(backendApiUrl, isProduction);
    res.variableUsed = "BACKEND_API_URL";
    return res;
  }

  // 2. Check NEXT_PUBLIC_API_URL (fallback if BACKEND_API_URL not provided)
  if (nextPublicApiUrl && !isPlaceholderValue(nextPublicApiUrl)) {
    const res = validateBackendUrl(nextPublicApiUrl, isProduction);
    res.variableUsed = "NEXT_PUBLIC_API_URL";
    return res;
  }

  // 3. In development, fallback to local FastAPI
  if (!isProduction) {
    return {
      isValid: true,
      rawUrl: "http://127.0.0.1:8000",
      normalizedUrl: "http://127.0.0.1:8000",
      isPlaceholder: false,
      variableUsed: "DEV_FALLBACK",
    };
  }

  // 4. In production without valid variable:
  // Check if placeholder was provided to give exact error feedback
  if (backendApiUrl) {
    const res = validateBackendUrl(backendApiUrl, isProduction);
    res.variableUsed = "BACKEND_API_URL";
    return res;
  }
  if (nextPublicApiUrl) {
    const res = validateBackendUrl(nextPublicApiUrl, isProduction);
    res.variableUsed = "NEXT_PUBLIC_API_URL";
    return res;
  }

  // Completely missing
  return validateBackendUrl(undefined, isProduction);
}

export function maskUrlForLogs(url: string): string {
  if (!url) return "(not configured)";
  try {
    const u = new URL(url);
    const hostParts = u.hostname.split(".");
    if (hostParts.length >= 3) {
      const sub = hostParts[0];
      const maskedSub = sub.length > 4 ? `${sub.slice(0, 3)}***` : `${sub}***`;
      return `${u.protocol}//${maskedSub}.${hostParts.slice(1).join(".")}${u.port ? `:${u.port}` : ""}`;
    }
    return `${u.protocol}//${u.host}`;
  } catch {
    return url.length > 8 ? `${url.slice(0, 4)}***` : "***";
  }
}

export function getScreeningEndpoints(baseUrl: string): string[] {
  const clean = baseUrl.replace(/\/$/, "");
  return [
    `${clean}/api/backend/screen`,
    `${clean}/api/screen`,
    `${clean}/screen`,
    `${clean}/api/v1/verify`,
  ];
}
