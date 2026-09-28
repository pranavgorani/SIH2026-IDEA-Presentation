// Base URL for API calls. In Vercel Services production, relative /api/backend is used.
export const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

function getAuthHeader(): Record<string, string> {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("trustid_token");
    if (token) {
      return { Authorization: `Bearer ${token}` };
    }
  }
  return {};
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = API_BASE ? `${API_BASE}${cleanEndpoint}` : cleanEndpoint;

  const headers = {
    "Content-Type": "application/json",
    ...getAuthHeader(),
    ...(options.headers || {}),
  };

  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    let errorMsg = `Request failed: ${res.statusText}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) errorMsg = errJson.detail;
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }
  return res.json();
}

export interface ScreeningErrorPayload {
  success: false;
  request_id?: string;
  case_id?: string;
  stage: string;
  code: string;
  message: string;
  recoverable?: boolean;
  user_action?: string;
  error?: {
    code: string;
    message: string;
    stage: string;
  };
  pipeline?: Array<{ stage: string; status: string; code?: string; message?: string }>;
  stages?: any[];
  debug_details?: any;
}

export class ScreeningException extends Error {
  stage: string;
  code: string;
  recoverable: boolean;
  requestId?: string;
  userAction?: string;
  pipeline?: any[];
  debugDetails?: any;

  constructor(payload: Partial<ScreeningErrorPayload> | string) {
    if (typeof payload === "string") {
      super(payload);
      this.stage = "SYSTEM";
      this.code = "NETWORK_ERROR";
      this.recoverable = true;
      this.userAction = "Retry screening or execute with local computer-vision fallback.";
    } else {
      const reason = payload.message || payload.error?.message || "Screening could not be completed.";
      super(reason);
      this.stage = payload.stage || payload.error?.stage || "PROCESSING";
      this.code = payload.code || payload.error?.code || "SCREENING_ERROR";
      this.recoverable = payload.recoverable ?? true;
      this.requestId = payload.request_id;
      this.userAction = payload.user_action || (this.recoverable ? "Retry screening or execute with local computer-vision fallback." : "Please inspect the uploaded document scan and re-upload in a supported format.");
      this.pipeline = payload.pipeline || payload.stages;
      this.debugDetails = payload.debug_details;
    }
  }
}

export const api = {
  // Auth
  login: async (username: string, password: string) => {
    const data = await apiFetch<any>("/api/backend/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    if (typeof window !== "undefined") {
      localStorage.setItem("trustid_token", data.access_token);
      localStorage.setItem("trustid_user", JSON.stringify(data.user));
    }
    return data;
  },

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("trustid_token");
      localStorage.removeItem("trustid_user");
    }
  },

  getCurrentUser: async () => {
    return apiFetch<any>("/api/backend/auth/me");
  },

  // Health
  getHealth: async () => {
    return apiFetch<any>("/api/backend/health");
  },

  getAIHealth: async () => {
    return apiFetch<any>("/api/backend/health/ai");
  },

  // Dashboard
  getDashboardStats: async () => {
    return apiFetch<any>("/api/backend/dashboard/stats");
  },

  // Cases
  listCases: async (filters: { risk_level?: string; document_type?: string; status?: string } = {}) => {
    const params = new URLSearchParams();
    if (filters.risk_level) params.append("risk_level", filters.risk_level);
    if (filters.document_type) params.append("document_type", filters.document_type);
    if (filters.status) params.append("status", filters.status);
    const qs = params.toString() ? `?${params.toString()}` : "";
    return apiFetch<any[]>(`/api/backend/cases${qs}`);
  },

  getCases: async (filters: { risk_level?: string; document_type?: string; status?: string; limit?: number } = {}) => {
    return api.listCases(filters);
  },

  getCaseDetails: async (caseId: string) => {
    return apiFetch<any>(`/api/backend/cases/${caseId}`);
  },

  submitReview: async (caseId: string, decision: string, reason: string) => {
    return apiFetch<any>(`/api/backend/cases/${caseId}/review`, {
      method: "POST",
      body: JSON.stringify({ decision, reason }),
    });
  },

  runDemoPreset: async (presetId: string) => {
    return apiFetch<any>(`/api/backend/cases/demo/${presetId}`, {
      method: "POST",
    });
  },

  // Screening with exponential backoff (attempt 1 immediate, 2 at 1s, 3 at 2s)
  screenDocument: async (
    formData: FormData,
    options?: { onRetryAttempt?: (attempt: number, maxAttempts: number) => void }
  ) => {
    const endpoint = "/api/backend/screen";
    const url = API_BASE ? `${API_BASE}${endpoint}` : endpoint;
    const maxAttempts = 3;
    const delays = [0, 1000, 2000];

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      if (attempt > 1) {
        options?.onRetryAttempt?.(attempt, maxAttempts);
        await new Promise((resolve) => setTimeout(resolve, delays[attempt - 1]));
      }

      let res: Response;
      try {
        res = await fetch(url, {
          method: "POST",
          headers: {
            ...getAuthHeader(),
          },
          body: formData,
        });
      } catch (netErr: any) {
        // Transient network failure: retry if attempts remaining
        if (attempt < maxAttempts) {
          continue;
        }
        throw new ScreeningException({
          success: false,
          stage: "GATEWAY",
          code: "BACKEND_CONNECTION_FAILED",
          message: "Unable to connect to TRUST-ID AI screening backend service. Please check connection.",
          recoverable: true,
          user_action: "Retry screening or execute with local computer-vision fallback.",
          debug_details: { error: netErr?.message }
        });
      }

      // Check if transient error (502 / 503) that warrants auto-retry
      if ((res.status === 502 || res.status === 503) && attempt < maxAttempts) {
        continue;
      }

      if (!res.ok) {
        let errPayload: any = null;
        let rawText = "";
        try {
          rawText = await res.text();
          errPayload = JSON.parse(rawText);
        } catch {
          // Response is non-JSON HTML (e.g. Next.js rewrite or nginx 500/502)
        }

        // Retry transient proxy connection drops (HTML 500 / 502 / 503)
        if (!errPayload && res.status >= 500 && attempt < maxAttempts) {
          options?.onRetryAttempt?.(attempt, maxAttempts);
          await new Promise((resolve) => setTimeout(resolve, delays[attempt] || 1000));
          continue;
        }

        const isClientError = res.status >= 400 && res.status < 500;
        const recoverable = errPayload?.recoverable ?? (!isClientError || res.status === 429);

        // Map status codes according to Section 8 of Gateway specification
        let stage = errPayload?.stage || errPayload?.error?.stage || (res.status >= 500 ? "GATEWAY" : "INPUT_VALIDATION");
        let code = errPayload?.code || errPayload?.error?.code || `HTTP_${res.status}`;
        let message = errPayload?.message || errPayload?.error?.message;

        if (!message) {
          if (res.status === 400) {
            code = code === `HTTP_${res.status}` ? "INVALID_DOCUMENT" : code;
            message = "Document format or payload is invalid. Supported: PDF, PNG, JPG, WEBP.";
          } else if (res.status === 401) {
            code = "UNAUTHORIZED";
            message = "Authentication required. Please log in.";
          } else if (res.status === 403) {
            code = "FORBIDDEN";
            message = "Insufficient permissions to execute screening.";
          } else if (res.status === 404) {
            code = "NOT_FOUND";
            message = "Screening endpoint or document not found.";
          } else if (res.status === 413) {
            code = "FILE_TOO_LARGE";
            message = "Uploaded file exceeds maximum allowed size (25MB).";
          } else if (res.status === 422) {
            code = "UNPROCESSABLE_ENTITY";
            message = "Document parameters cannot be processed. Please check document orientation and format.";
          } else if (res.status === 429) {
            code = "RATE_LIMITED";
            message = "Too many requests. Please wait a moment before retrying.";
          } else if (res.status === 502 || res.status === 503) {
            code = "SERVICE_UNAVAILABLE";
            message = "Screening backend service is temporarily unavailable. Please retry.";
          } else {
            code = "SERVICE_ERROR";
            message = `Screening service returned HTTP ${res.status} (${res.statusText || "Service Error"})`;
          }
        }

        throw new ScreeningException({
          success: false,
          request_id: errPayload?.request_id || res.headers.get("x-request-id") || undefined,
          case_id: errPayload?.case_id,
          stage,
          code,
          message,
          recoverable,
          user_action: errPayload?.user_action,
          pipeline: errPayload?.pipeline || errPayload?.stages,
          debug_details: {
            status: res.status,
            statusText: res.statusText,
            url: res.url,
            rawBody: rawText ? rawText.slice(0, 500) : undefined
          }
        });
      }

      return res.json();
    }
  },

  // Audit
  getAuditLog: async (caseId: string) => {
    return apiFetch<any[]>(`/api/backend/audit/${caseId}`);
  },

  verifyAuditIntegrity: async (caseId: string) => {
    return apiFetch<any>(`/api/backend/audit/${caseId}/verify`);
  },

  // Admin & System
  getSettings: async () => {
    return apiFetch<any>("/api/backend/settings");
  },

  updateSettings: async (settings: any) => {
    return apiFetch<any>("/api/backend/settings", {
      method: "PUT",
      body: JSON.stringify(settings),
    });
  },

  getSystemHealth: async () => {
    return apiFetch<any>("/api/backend/settings/health");
  },

  // 100-Checks & Reports
  getCaseChecks: async (caseId: string) => {
    return apiFetch<any>(`/api/backend/cases/${caseId}/checks`);
  },

  getCaseReport: async (caseId: string) => {
    return apiFetch<any>(`/api/backend/cases/${caseId}/report`);
  },

  getGlobalReports: async (params: { risk_level?: string; document_type?: string; limit?: number } = {}) => {
    const q = new URLSearchParams();
    if (params.risk_level) q.append("risk_level", params.risk_level);
    if (params.document_type) q.append("document_type", params.document_type);
    if (params.limit) q.append("limit", params.limit.toString());
    const queryStr = q.toString() ? `?${q.toString()}` : "";
    return apiFetch<any>(`/api/backend/reports${queryStr}`);
  },

  addInvestigationNote: async (caseId: string, note: { note_type: string; content: string }) => {
    return apiFetch<any>(`/api/backend/cases/${caseId}/investigation-notes`, {
      method: "POST",
      body: JSON.stringify(note),
    });
  },

  // 100-Document Benchmark & Border Stream Simulator
  getBenchmark100: async (seed?: number) => {
    const q = seed !== undefined ? `?seed=${seed}` : "";
    return apiFetch<any>(`/api/backend/dashboard/benchmark-100${q}`);
  },

  runBenchmark100: async () => {
    return apiFetch<any>("/api/backend/dashboard/benchmark-100/run", {
      method: "POST",
    });
  },
};

// Standalone named exports for convenient importing
export const runDemoPreset = (presetId: string) => api.runDemoPreset(presetId);
export const getSystemSettings = () => api.getSettings();
export const updateSystemSettings = (s: any) => api.updateSettings(s);
export const getSystemHealth = () => api.getSystemHealth();
