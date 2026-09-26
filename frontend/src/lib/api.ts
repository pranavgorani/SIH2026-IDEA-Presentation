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
    const res = await fetch(url, {
      method: "POST",
      headers: {
        ...getAuthHeader(),
      },
      body: formData,
    });
    if (!res.ok) {
      let msg = "Screening failed";
      try {
        const j = await res.json();
        if (j.detail) msg = j.detail;
      } catch {}
      throw new Error(msg);
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
};

// Standalone named exports for convenient importing
export const runDemoPreset = (presetId: string) => api.runDemoPreset(presetId);
export const getSystemSettings = () => api.getSettings();
export const updateSystemSettings = (s: any) => api.updateSettings(s);
export const getSystemHealth = () => api.getSystemHealth();
