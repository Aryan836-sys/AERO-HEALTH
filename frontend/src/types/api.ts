/**
 * Provisional frontend DTOs, NOT generated from a real backend.
 * The supplied project guide contains endpoint names but no OpenAPI schema.
 * Keep these in sync with contracts/openapi.demo.json until the team supplies one.
 * `npm run types:generate` writes the real generated schema to api.generated.ts;
 * reconcile the service adapter before replacing this provisional contract.
 */
export type District = 'Kathmandu' | 'Lalitpur' | 'Bhaktapur';
export type Reliability = 'official' | 'community' | 'modelled';
export type Pollutant = 'PM2.5' | 'PM10' | 'O3' | 'NO2' | 'SO2' | 'CO';
export type CategoryKey = 'good' | 'moderate' | 'sensitive' | 'unhealthy' | 'veryUnhealthy' | 'hazardous';
export type Range = '24h' | '7d' | '30d';
export interface Reading {
  aqi: number;
  mainPollutant: Pollutant;
  pollutants: Record<Pollutant, number>;
  source: string;
  reliability: Reliability;
  observedAt: string;
  weather: {
    temperature: number;
    humidity: number;
    windSpeed: number;
    windDirection: string;
  };
  isDemo: boolean;
}
export interface Area {
  id: string;
  name: string;
  nameNe: string;
  district: District;
  latitude: number;
  longitude: number;
  reading: Reading | null;
  description: string;
  featured?: boolean;
}
export interface TrendPoint {
  time: string;
  aqi: number | null;
  forecast?: number | null;
}
export interface User {
  id: string;
  name: string;
  email: string;
  role: 'user' | 'admin';
}
export interface Session {
  user: User;
  accessToken: string;
}
export type HealthFlag = 'asthma' | 'respiratory' | 'heart' | 'pregnancy' | 'outdoorWorker';
export interface HealthProfile {
  ageGroup: '' | 'child' | 'adult' | 'older';
  conditions: HealthFlag[];
  activityLevel: '' | 'low' | 'moderate' | 'high';
  preferredLanguage: 'en' | 'ne';
}
export interface Advisory {
  level: 'low' | 'elevated' | 'high';
  recommendationKey: string;
  reasons: {
    key: string;
    values?: Record<string, string | number>;
  }[];
  aqi: number;
  personalized: boolean;
  isDemo: boolean;
}
export type ReportCategory = 'dust' | 'burning' | 'traffic' | 'industrial' | 'other';
export type ReportStatus = 'unverified' | 'verified' | 'rejected' | 'flagged';
export interface PollutionReport {
  id: string;
  category: ReportCategory;
  description: string;
  areaId: string;
  latitude: number;
  longitude: number;
  anonymous: boolean;
  author: string;
  status: ReportStatus;
  createdAt: string;
  photo?: string;
  isDemo: boolean;
}
export interface AlertRule {
  id: string;
  areaId: string;
  threshold: number;
  channel: 'in-app' | 'email';
  enabled: boolean;
}
export interface AdminStats {
  users: number;
  reports: number;
  pending: number;
  flagged: number;
}
export interface ApiService {
  getLocations(): Promise<Area[]>;
  getTrend(id: string, range: Range): Promise<TrendPoint[]>;
  compare(a: string, b: string): Promise<Area[]>;
  login(email: string, password: string): Promise<Session>;
  register(name: string, email: string, password: string): Promise<Session>;
  refresh(): Promise<Session | null>;
  logout(): Promise<void>;
  getProfile(): Promise<HealthProfile | null>;
  saveProfile(profile: HealthProfile): Promise<HealthProfile>;
  deleteProfile(): Promise<void>;
  getAdvisory(areaId: string, profile: HealthProfile | null): Promise<Advisory>;
  getFavorites(): Promise<string[]>;
  setFavorite(areaId: string, saved: boolean): Promise<string[]>;
  getAlerts(): Promise<AlertRule[]>;
  saveAlert(alert: Omit<AlertRule, 'id'>): Promise<AlertRule[]>;
  toggleAlert(id: string): Promise<AlertRule[]>;
  deleteAlert(id: string): Promise<AlertRule[]>;
  getReports(): Promise<PollutionReport[]>;
  submitReport(data: FormData, onProgress: (percent: number) => void): Promise<PollutionReport>;
  moderateReport(id: string, status: ReportStatus): Promise<PollutionReport>;
  getAdminStats(): Promise<AdminStats>;
}
