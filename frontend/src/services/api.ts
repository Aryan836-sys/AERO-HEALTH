import axios from 'axios';
import type { ApiService, Session, HealthProfile } from '../types/api';
import { mockApi } from './mockApi';
import {
  toAdvisory, toAlert, toApiCategory, toApiProfile, toArea, toAreas, toHealthProfile, toReport,
  toSession, toStats, toTrendPoint,
  type ApiAdvisory, type ApiAlert, type ApiLocation, type ApiProfile, type ApiReading, type ApiReport,
  type ApiStats, type ApiTokenPair, type ApiUser,
} from './mappers';
import type { components } from '../types/api.generated';
export const IS_DEMO = import.meta.env.VITE_USE_MOCK_API !== 'false';
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
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
  baseURL: API_BASE,
  timeout: 15000,
  // The refresh token lives in an HttpOnly cookie set by the backend.
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
    refreshing = axios.post<ApiTokenPair>(`${API_BASE}/auth/refresh`, {}, { withCredentials: true, timeout: 15000 })
      .then(({ data }) => { const session = toSession(data); setAccessToken(session.accessToken); return session; })
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
    if (session) {
      // Re-issue with the fresh token (the request interceptor won't run again for the stored config).
      config.headers.Authorization = `Bearer ${session.accessToken}`;
      return http(config);
    }
    window.dispatchEvent(new Event('aero:session-expired'));
  }
  const data = error.response?.data as {
    detail?: unknown;
    errors?: { field?: string; message?: string }[];
  } | undefined;
  // Backend validation errors list the offending fields; show the first one.
  const firstField = data?.errors?.[0];
  const detail = firstField?.message
    ? `${firstField.field ? `${firstField.field}: ` : ''}${firstField.message}`
    : data?.detail;
  return Promise.reject(new ApiError(typeof detail === 'string' ? detail : error.response ? `Request failed (${error.response.status}). Please try again.` : 'Cannot reach the API. Check your connection and backend configuration.', error.response?.status));
});
const isNotFound = (error: unknown) => error instanceof ApiError && error.status === 404;
async function currentLanguage(): Promise<'en' | 'ne'> {
  const { data } = await http.get<ApiUser>('/me');
  return data.preferred_language === 'ne' ? 'ne' : 'en';
}
async function listFavorites(): Promise<string[]> {
  const { data } = await http.get<components['schemas']['FavoriteOut'][]>('/favorites');
  return data.map((favorite) => String(favorite.location_id));
}
async function listAlerts() {
  return (await http.get<ApiAlert[]>('/alerts')).data.map(toAlert);
}
// Wire format: see types/api.generated.ts. Mapping to UI types: services/mappers.ts.
const realApi: ApiService = {
  getLocations: async () => toAreas((await http.get<ApiLocation[]>('/locations')).data),
  getTrend: async (id, range) => (await http.get<ApiReading[]>(`/readings/${encodeURIComponent(id)}`, { params: { range } })).data.map(toTrendPoint),
  compare: async (a, b) => {
    const { data } = await http.get<components['schemas']['CompareOut']>('/locations/compare', { params: { a, b } });
    return [toArea(data.a), toArea(data.b)];
  },
  login: async (email, password) => {
    const session = toSession((await http.post<ApiTokenPair>('/auth/login', { email, password })).data);
    setAccessToken(session.accessToken);
    return session;
  },
  register: async (name, email, password) => {
    await http.post('/auth/register', { full_name: name, email, password });
    return realApi.login(email, password);
  },
  refresh: refreshSession,
  logout: async () => {
    try {
      await http.post('/auth/logout');
    }
    finally {
      setAccessToken(null);
    }
  },
  getProfile: async () => {
    try {
      const [{ data }, language] = await Promise.all([http.get<ApiProfile>('/profile'), currentLanguage()]);
      return toHealthProfile(data, language);
    }
    catch (error) {
      if (isNotFound(error))
        return null;
      throw error;
    }
  },
  saveProfile: async (profile: HealthProfile) => {
    const body = toApiProfile(profile);
    let saved: ApiProfile;
    try {
      saved = (await http.put<ApiProfile>('/profile', body)).data;
    }
    catch (error) {
      if (!isNotFound(error))
        throw error;
      saved = (await http.post<ApiProfile>('/profile', body)).data;
    }
    // Language belongs to the account, not the health profile.
    await http.patch('/me', { preferred_language: profile.preferredLanguage });
    return toHealthProfile(saved, profile.preferredLanguage);
  },
  deleteProfile: async () => { await http.delete('/profile'); },
  getAdvisory: async (areaId, profile) => toAdvisory((await http.post<ApiAdvisory>('/advisory', {
    location_id: Number(areaId),
    // A what-if profile (e.g. the Advisory page examples); null falls back to the caller's stored one.
    profile: profile ? toApiProfile(profile) : undefined,
  })).data),
  getFavorites: listFavorites,
  setFavorite: async (areaId, saved) => {
    if (saved)
      await http.post('/favorites', { location_id: Number(areaId) });
    else
      await http.delete(`/favorites/${encodeURIComponent(areaId)}`);
    return listFavorites();
  },
  getAlerts: listAlerts,
  saveAlert: async (alert) => {
    await http.post('/alerts', { location_id: Number(alert.areaId), aqi_threshold: alert.threshold, notification_type: alert.channel });
    return listAlerts();
  },
  toggleAlert: async (id) => {
    const current = (await listAlerts()).find((alert) => alert.id === id);
    if (!current)
      throw new ApiError('This alert no longer exists.', 404);
    await http.patch(`/alerts/${encodeURIComponent(id)}`, { active: !current.enabled });
    return listAlerts();
  },
  deleteAlert: async (id) => { await http.delete(`/alerts/${encodeURIComponent(id)}`); return listAlerts(); },
  getReports: async () => (await http.get<ApiReport[]>('/reports', { params: { limit: 100 } })).data.map((report) => toReport(report, API_BASE)),
  getModerationReports: async () => (await http.get<ApiReport[]>('/admin/reports', { params: { status: 'all' } })).data.map((report) => toReport(report, API_BASE)),
  submitReport: async (form, progress) => {
    // The form speaks the UI's vocabulary; translate it for the backend.
    // Only coordinates are sent: the backend snaps them to the nearest station.
    const body = new FormData();
    body.set('category', toApiCategory(String(form.get('category')) as Parameters<typeof toApiCategory>[0]));
    body.set('description', String(form.get('description') ?? ''));
    body.set('latitude', String(form.get('latitude')));
    body.set('longitude', String(form.get('longitude')));
    body.set('anonymous', String(form.get('anonymous') !== 'false'));
    const photo = form.get('photo');
    if (photo instanceof File && photo.size > 0)
      body.set('image', photo);
    const { data } = await http.post<ApiReport>('/reports', body, { onUploadProgress: (event) => progress(event.total ? Math.round(event.loaded / event.total * 100) : 0) });
    return toReport(data, API_BASE);
  },
  moderateReport: async (id, status) => toReport((await http.patch<ApiReport>(`/admin/reports/${encodeURIComponent(id)}`, { verification_status: status })).data, API_BASE),
  getAdminStats: async () => toStats((await http.get<ApiStats>('/admin/stats')).data),
};
export const api: ApiService = IS_DEMO ? mockApi : realApi;
