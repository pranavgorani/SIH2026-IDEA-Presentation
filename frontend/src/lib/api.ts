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
  case_id?: string;
  stage: string;
  code: string;
  message: string;
  recoverable?: boolean;
  error?: {
    code: string;
    message: string;
    stage: string;
  };
  pipeline?: Array<{ stage: string; status: string; code?: string; message?: string }>;
}

export class ScreeningException extends Error {
  stage: string;
  code: string;
  recoverable: boolean;
  pipeline?: any[];

  constructor(payload: Partial<ScreeningErrorPayload> | string) {
    if (typeof payload === "string") {
      super(payload);
      this.stage = "SYSTEM";
      this.code = "NETWORK_ERROR";
      this.recoverable = true;
    } else {
      const reason = payload.message || payload.error?.message || "Screening could not be completed.";
      super(reason);
      this.stage = payload.stage || payload.error?.stage || "PROCESSING";
      this.code = payload.code || payload.error?.code || "SCREENING_ERROR";
      this.recoverable = payload.recoverable ?? true;
      this.pipeline = payload.pipeline;
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

  // Screening
  screenDocument: async (formData: FormData) => {
    const endpoint = "/api/backend/screen";
    const url = API_BASE ? `${API_BASE}${endpoint}` : endpoint;
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
      throw new ScreeningException({
        success: false,
        stage: "GATEWAY",
        code: "BACKEND_CONNECTION_FAILED",
        message: "Unable to connect to TRUST-ID AI screening backend service. Please check connection.",
        recoverable: true
      });
    }

    if (!res.ok) {
      let errPayload: any = null;
      try {
        errPayload = await res.json();
      } catch {}

      if (errPayload && typeof errPayload === "object") {
        throw new ScreeningException({
          success: false,
          case_id: errPayload.case_id,
          stage: errPayload.stage || errPayload.error?.stage || "PROCESSING",
          code: errPayload.code || errPayload.error?.code || "HTTP_ERROR",
          message: errPayload.message || errPayload.error?.message || (typeof errPayload.detail === "string" ? errPayload.detail : `Request failed (${res.status})`),
          recoverable: errPayload.recoverable ?? (res.status < 500),
          pipeline: errPayload.pipeline
        });
      }

      throw new ScreeningException({
        success: false,
        stage: "GATEWAY",
        code: `HTTP_${res.status}`,
        message: `Screening service returned HTTP ${res.status} (${res.statusText || "Service Error"})`,
        recoverable: true
      });
    }
    return res.json();
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
};

// Standalone named exports for convenient importing
export const runDemoPreset = (presetId: string) => api.runDemoPreset(presetId);
export const getSystemSettings = () => api.getSettings();
export const updateSystemSettings = (s: any) => api.updateSettings(s);
export const getSystemHealth = () => api.getSystemHealth();
