// SIH26028 — shared backend client for the React dashboard.
// All calls go to the FastAPI backend on 127.0.0.1:8000.
// When the backend is unavailable every call throws ApiError with
// status 0, so the UI can fall back to the built-in demo simulation.

const API_BASE = "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, { method = "GET", body, token } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let resp;
  try {
    resp = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined
    });
  } catch (err) {
    throw new ApiError(`FastAPI unreachable at ${API_BASE}`, 0);
  }

  if (resp.status === 204) return null;

  let data = null;
  try {
    data = await resp.json();
  } catch (err) {
    throw new ApiError(`Invalid response from API (HTTP ${resp.status}).`, resp.status);
  }

  if (!resp.ok) {
    let detail = `HTTP ${resp.status}`;
    if (data && data.detail) {
      detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    }
    throw new ApiError(detail, resp.status);
  }

  return data;
}

export const api = {
  base: API_BASE,

  checkHealth: () => request("/health"),

  login: (username, password) =>
    request("/login", { method: "POST", body: { username, password } }),

  logout: (token) =>
    request("/logout", { method: "POST", token }),

  fetchEta: (payload, token) =>
    request("/predict-eta", { method: "POST", body: payload, token }),

  fetchAssistance: (payload, token) =>
    request("/passenger-assistance", { method: "POST", body: payload, token }),

  submitDelayReport: (payload, token) =>
    request("/copilot/delay-report", { method: "POST", body: payload, token }),

  fetchReports: (token, status) =>
    request(`/control-room/reports${status ? `?status=${status}` : ""}`, { token }),

  acknowledgeReport: (reportId, token) =>
    request(`/control-room/reports/${reportId}/acknowledge`, { method: "POST", token }),

  fetchTrainStatus: (trainNumber, token) =>
    request(`/train/${trainNumber}/status`, { token })
};