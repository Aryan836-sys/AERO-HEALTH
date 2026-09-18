import axios from 'axios';
import type { ApiService, Session, HealthProfile, Area, TrendPoint, AlertRule, PollutionReport, Advisory, AdminStats } from '../types/api';
import { mockApi } from './mockApi';
export const IS_DEMO = import.meta.env.VITE_USE_MOCK_API !== 'false';
/** Carries an HTTP status without exposing raw backend payloads to components. */
export class ApiError extends Error {
  constructor(message: string, public readonly status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}
let accessToken: string | null = null;
export function setAccessToken(token: string | null): void { accessToken = token; }
export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 15000,
  withCredentials: true,
  headers: { Accept: 'application/json' },
});
http.interceptors.request.use((config) => {
  if (accessToken)
    config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
});
let refreshing: Promise<Session | null> | null = null;
async function refreshSession(): Promise<Session | null> {
  if (!refreshing) {
    refreshing = axios.post<Session>(`${http.defaults.baseURL}/auth/refresh`, {}, { withCredentials: true, timeout: 15000 })
      .then(({ data }) => { setAccessToken(data.accessToken); return data; })
      .catch(() => { setAccessToken(null); return null; })
      .finally(() => { refreshing = null; });
  }
  return refreshing;
}
http.interceptors.response.use((response) => response, async (error: unknown) => {
  if (!axios.isAxiosError(error))
    return Promise.reject(error);
  const config = error.config as (typeof error.config & {
    _retried?: boolean;
  });
  if (error.response?.status === 401 && config && !config._retried && !config.url?.startsWith('/auth/')) {
    config._retried = true;
    const session = await refreshSession();
    if (session)
      return http(config);
    window.dispatchEvent(new Event('aero:session-expired'));
  }
  const detail = (error.response?.data as {
    detail?: unknown;
  } | undefined)?.detail;
  return Promise.reject(new ApiError(typeof detail === 'string' ? detail : error.response ? `Request failed (${error.response.status}). Please try again.` : 'Cannot reach the API. Check your connection and backend configuration.', error.response?.status));
});
// Assumed DTOs only: reconcile against your team's OpenAPI before enabling real mode.
const realApi: ApiService = {
  getLocations: async () => (await http.get<Area[]>('/locations')).data,
  getTrend: async (id, range) => (await http.get<TrendPoint[]>(`/readings/${encodeURIComponent(id)}`, { params: { range } })).data,
  compare: async (a, b) => (await http.get<Area[]>('/locations/compare', { params: { a, b } })).data,
  login: async (email, password) => (await http.post<Session>('/auth/login', { email, password })).data,
  register: async (name, email, password) => (await http.post<Session>('/auth/register', { name, email, password })).data,
  refresh: refreshSession,
  logout: async () => { await http.post('/auth/logout'); setAccessToken(null); },
  getProfile: async () => {
    try {
      return (await http.get<HealthProfile | null>('/profile')).data;
    }
    catch (error) {
      if (error instanceof ApiError && error.status === 404)
        return null;
      throw error;
    }
  },
  saveProfile: async (profile) => {
    const existing = await realApi.getProfile();
    return existing ? (await http.put<HealthProfile>('/profile', profile)).data : (await http.post<HealthProfile>('/profile', profile)).data;
  },
  deleteProfile: async () => { await http.delete('/profile'); },
  getAdvisory: async (areaId, profile) => (await http.post<Advisory>('/advisory', { location_id: areaId, profile })).data,
  getFavorites: async () => (await http.get<string[]>('/favorites')).data,
  setFavorite: async (areaId, saved) => {
    if (saved)
      await http.post('/favorites', { location_id: areaId });
    else
      await http.delete(`/favorites/${encodeURIComponent(areaId)}`);
    return realApi.getFavorites();
  },
  getAlerts: async () => (await http.get<AlertRule[]>('/alerts')).data,
  saveAlert: async (alert) => { await http.post('/alerts', alert); return realApi.getAlerts(); },
  toggleAlert: async (id) => { await http.patch(`/alerts/${encodeURIComponent(id)}/toggle`); return realApi.getAlerts(); },
  deleteAlert: async (id) => { await http.delete(`/alerts/${encodeURIComponent(id)}`); return realApi.getAlerts(); },
  getReports: async () => (await http.get<PollutionReport[]>('/reports')).data,
  submitReport: async (form, progress) => (await http.post<PollutionReport>('/reports', form, { onUploadProgress: (event) => progress(event.total ? Math.round(event.loaded / event.total * 100) : 0) })).data,
  moderateReport: async (id, status) => (await http.patch<PollutionReport>(`/admin/reports/${encodeURIComponent(id)}`, { status })).data,
  getAdminStats: async () => (await http.get<AdminStats>('/admin/stats')).data,
};
export const api: ApiService = IS_DEMO ? mockApi : realApi;
