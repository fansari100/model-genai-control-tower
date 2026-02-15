// ─────────────────────────────────────────────────────────────
// Control Tower – API Client
// ─────────────────────────────────────────────────────────────

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_V1 = `${API_BASE}/api/v1`;

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_V1}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }
  return res.json();
}

// ── Dashboard ───────────────────────────────────────────────
export const dashboard = {
  getSummary: () => fetchAPI<any>("/dashboard/summary"),
  getCommitteeReport: () => fetchAPI<any>("/dashboard/committee-report"),
};

// ── Vendors ─────────────────────────────────────────────────
export const vendors = {
  list: (params?: string) => fetchAPI<any>(`/vendors${params ? `?${params}` : ""}`),
  get: (id: string) => fetchAPI<any>(`/vendors/${id}`),
  create: (data: any) => fetchAPI<any>("/vendors", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: any) => fetchAPI<any>(`/vendors/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  delete: (id: string) => fetchAPI<void>(`/vendors/${id}`, { method: "DELETE" }),
};

// ── Models ──────────────────────────────────────────────────
export const models = {
  list: (params?: string) => fetchAPI<any>(`/models${params ? `?${params}` : ""}`),
  get: (id: string) => fetchAPI<any>(`/models/${id}`),
  create: (data: any) => fetchAPI<any>("/models", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: any) => fetchAPI<any>(`/models/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  delete: (id: string) => fetchAPI<void>(`/models/${id}`, { method: "DELETE" }),
  transition: (id: string, status: string) =>
    fetchAPI<any>(`/models/${id}/transition?new_status=${status}`, { method: "POST" }),
};

// ── Tools ───────────────────────────────────────────────────
export const tools = {
  list: (params?: string) => fetchAPI<any>(`/tools${params ? `?${params}` : ""}`),
  get: (id: string) => fetchAPI<any>(`/tools/${id}`),
  create: (data: any) => fetchAPI<any>("/tools", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: any) => fetchAPI<any>(`/tools/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  delete: (id: string) => fetchAPI<void>(`/tools/${id}`, { method: "DELETE" }),
  attest: (id: string) => fetchAPI<any>(`/tools/${id}/attest`, { method: "POST" }),
};

// ── Use Cases ───────────────────────────────────────────────
export const useCases = {
  list: (params?: string) => fetchAPI<any>(`/use-cases${params ? `?${params}` : ""}`),
  get: (id: string) => fetchAPI<any>(`/use-cases/${id}`),
  create: (data: any) => fetchAPI<any>("/use-cases", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: any) => fetchAPI<any>(`/use-cases/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  delete: (id: string) => fetchAPI<void>(`/use-cases/${id}`, { method: "DELETE" }),
  intake: (data: any) => fetchAPI<any>("/use-cases/intake", { method: "POST", body: JSON.stringify(data) }),
};

// ── Evaluations ─────────────────────────────────────────────
export const evaluations = {
  list: (params?: string) => fetchAPI<any>(`/evaluations${params ? `?${params}` : ""}`),
  get: (id: string) => fetchAPI<any>(`/evaluations/${id}`),
  getResults: (id: string) => fetchAPI<any>(`/evaluations/${id}/results`),
  create: (data: any) => fetchAPI<any>("/evaluations", { method: "POST", body: JSON.stringify(data) }),
  trigger: (data: any) => fetchAPI<any>("/evaluations/trigger", { method: "POST", body: JSON.stringify(data) }),
};

// ── Findings ────────────────────────────────────────────────
export const findings = {
  list: (params?: string) => fetchAPI<any>(`/findings${params ? `?${params}` : ""}`),
  get: (id: string) => fetchAPI<any>(`/findings/${id}`),
  create: (data: any) => fetchAPI<any>("/findings", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: any) => fetchAPI<any>(`/findings/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
};

// ── Approvals ───────────────────────────────────────────────
export const approvals = {
  list: (params?: string) => fetchAPI<any>(`/approvals${params ? `?${params}` : ""}`),
  get: (id: string) => fetchAPI<any>(`/approvals/${id}`),
  create: (data: any) => fetchAPI<any>("/approvals", { method: "POST", body: JSON.stringify(data) }),
};

// ── Evidence ────────────────────────────────────────────────
export const evidence = {
  list: (params?: string) => fetchAPI<any>(`/evidence${params ? `?${params}` : ""}`),
  get: (id: string) => fetchAPI<any>(`/evidence/${id}`),
  verify: (id: string) => fetchAPI<any>(`/evidence/${id}/verify`),
};

// ── Certifications ──────────────────────────────────────────
export const certifications = {
  generate: (data: any) => fetchAPI<any>("/certifications/generate", { method: "POST", body: JSON.stringify(data) }),
};

// ── Monitoring ──────────────────────────────────────────────
export const monitoring = {
  listPlans: (params?: string) => fetchAPI<any>(`/monitoring/plans${params ? `?${params}` : ""}`),
  getPlan: (id: string) => fetchAPI<any>(`/monitoring/plans/${id}`),
  createPlan: (data: any) => fetchAPI<any>("/monitoring/plans", { method: "POST", body: JSON.stringify(data) }),
  listExecutions: (planId: string) => fetchAPI<any>(`/monitoring/plans/${planId}/executions`),
  triggerExecution: (planId: string) => fetchAPI<any>(`/monitoring/plans/${planId}/execute`, { method: "POST" }),
};
