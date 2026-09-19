import axios from 'axios';
import type {
  Train,
  TrainLiveResponse,
  TrainPosition,
  Station,
  ETAResponse,
  WeatherResponse,
  StationReport,
  Alert,
  CongestionState,
  SimulationStatus,
  SimulationScenario,
  PaginatedResponse,
  ListResponse,
  HealthResponse,
} from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  register: (data: { username: string; email: string; full_name: string; password: string; role?: string }) =>
    api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
};

export const trainApi = {
  list: (params?: { page?: number; page_size?: number; status?: string; train_type?: string }) =>
    api.get<ListResponse<Train>>('/trains', { params }),
  get: (id: number) => api.get<Train>(`/trains/${id}`),
  getByNumber: (number: string) => api.get<Train>(`/trains/number/${number}`),
  getLive: (id: number) => api.get<TrainLiveResponse>(`/trains/${id}/live`),
  getRoute: (id: number) => api.get(`/trains/${id}/route`),
  getPositions: (id: number, params?: { limit?: number; since?: string }) =>
    api.get<TrainPosition[]>(`/trains/${id}/positions`, { params }),
  getEvents: (id: number, params?: { limit?: number; since?: string }) =>
    api.get(`/trains/${id}/events`, { params }),
  create: (data: Partial<Train>) => api.post<Train>('/trains', data),
  update: (id: number, data: Partial<Train>) => api.patch<Train>(`/trains/${id}`, data),
  delete: (id: number) => api.delete(`/trains/${id}`),
};

export const stationApi = {
  list: (params?: { page?: number; page_size?: number }) =>
    api.get<PaginatedResponse<Station>>('/stations', { params }),
  get: (id: number) => api.get<Station>(`/stations/${id}`),
  getByCode: (code: string) => api.get<Station>(`/stations/code/${code}`),
  getReports: (stationId: number, params?: { train_id?: number; status?: string; page?: number; page_size?: number }) =>
    api.get<PaginatedResponse<StationReport>>(`/stations/${stationId}/reports`, { params }),
  getEvents: (stationId: number, params?: { train_id?: number; limit?: number }) =>
    api.get(`/stations/${stationId}/events`, { params }),
  createReport: (stationId: number, data: Partial<StationReport>) =>
    api.post<StationReport>(`/stations/${stationId}/reports`, data),
  updateReport: (reportId: number, data: Partial<StationReport>) =>
    api.patch<StationReport>(`/stations/reports/${reportId}`, data),
};

export const predictionApi = {
  getETA: (trainNumber: string, params?: { include_explanations?: boolean; include_uncertainty?: boolean }) =>
    api.get<ETAResponse>(`/predictions/eta/${trainNumber}`, { params }),
  predictETA: (trainNumber: string, data?: { include_explanations?: boolean; include_uncertainty?: boolean }) =>
    api.post<ETAResponse>('/predictions/eta', { train_number: trainNumber, ...data }),
};

export const weatherApi = {
  getStationWeather: (stationId: number) => api.get<WeatherResponse>(`/weather/station/${stationId}`),
  getByCoordinates: (lat: number, lon: number) => api.get<WeatherResponse>(`/weather/coordinates`, { params: { lat, lon } }),
  getRouteWeather: (trainId: number, limit?: number) => api.get<WeatherResponse[]>(`/weather/route/${trainId}`, { params: { limit } }),
};

export const alertApi = {
  list: (params?: { train_id?: number; station_id?: number; severity?: string; active_only?: boolean }) =>
    api.get<Alert[]>('/alerts', { params }),
  acknowledge: (id: number) => api.post(`/alerts/${id}/acknowledge`),
  resolve: (id: number) => api.post(`/alerts/${id}/resolve`),
  generateForTrain: (trainId: number) => api.post<Alert[]>(`/alerts/train/${trainId}/generate`),
};

export const congestionApi = {
  getNetwork: () => api.get<CongestionState[]>('/congestion/network'),
  getSection: (sectionId: number, timeWindow?: number) =>
    api.get<CongestionState>(`/congestion/section/${sectionId}`, { params: { time_window_minutes: timeWindow } }),
  getStation: (stationId: number, timeWindow?: number) =>
    api.get<CongestionState>(`/congestion/station/${stationId}`, { params: { time_window_minutes: timeWindow } }),
};

export const simulationApi = {
  getStatus: () => api.get<SimulationStatus>('/simulation/status'),
  control: (action: string, speed?: number, scenario?: SimulationScenario) =>
    api.post('/simulation/control', { action, speed, scenario }),
  whatIf: (trainNumber: string, scenarioType: string, parameters: Record<string, unknown>, duration?: number) =>
    api.post('/simulation/what-if', { train_number: trainNumber, scenario_type: scenarioType, parameters, simulation_duration_minutes: duration }),
};

export const healthApi = {
  check: () => api.get<HealthResponse>('/health'),
};

export default api;