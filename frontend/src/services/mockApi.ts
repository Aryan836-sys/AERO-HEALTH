import type { ApiService, AlertRule, HealthProfile, PollutionReport, ReportStatus, Session, User } from '../types/api';
import { DEMO_AREAS, DEMO_REPORTS, demoTrend } from './fixtures';
import { makeDemoAdvisory } from '../utils/advisory';
import { isInValley } from '../utils/geo';
import { validEmail, validThreshold, validatePhoto } from '../utils/validation';
import { readStored, writeStored, removeStored, notifyDataChanged } from './storage';
export const DEMO_CREDENTIALS = {
  user: { email: 'demo@aerohealth.local', password: 'AeroDemo2026!' },
  admin: { email: 'admin@aerohealth.local', password: 'AeroAdmin2026!' },
} as const;
const BUILTIN_USERS: User[] = [
  { id: 'demo-user', name: 'Aarav', email: DEMO_CREDENTIALS.user.email, role: 'user' },
  { id: 'demo-admin', name: 'Aero Moderator', email: DEMO_CREDENTIALS.admin.email, role: 'admin' },
];
interface DemoAccount {
  user: User;
  passwordHash: string;
}
const wait = (ms = 320) => new Promise<void>((resolve) => setTimeout(resolve, ms));
const clone = <T,>(value: T): T => structuredClone(value);
function currentUser(): User | null {
  const id = readStored<string | null>('demo-session', null, true);
  const accounts = readStored<DemoAccount[]>('demo-accounts', [], true);
  return [...BUILTIN_USERS, ...accounts.map((account) => account.user)].find((user) => user.id === id) ?? null;
}
function requireUser(): User {
  const user = currentUser();
  if (!user)
    throw new Error('Please sign in to continue.');
  return user;
}
function requireAdmin(): User {
  const user = requireUser();
  if (user.role !== 'admin')
    throw new Error('Only a demo administrator can perform this action.');
  return user;
}
function beginSession(user: User): Session {
  // Only the demo user ID is stored. This is not a production authentication scheme.
  writeStored('demo-session', user.id, true);
  return { user: clone(user), accessToken: `demo-only-${crypto.randomUUID()}` };
}
async function hashPassword(email: string, password: string): Promise<string> {
  const buffer = new TextEncoder().encode(`aero-demo:${email}:${password}`);
  const digest = await crypto.subtle.digest('SHA-256', buffer);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}
function readReports(): PollutionReport[] { return readStored('reports', clone(DEMO_REPORTS)); }
function persistReports(reports: PollutionReport[]): void { writeStored('reports', reports); notifyDataChanged(); }
async function photoDataUrl(file: File): Promise<string> {
  // Decode before accepting a file, downsize before local demo persistence.
  const bitmap = await createImageBitmap(file);
  try {
    const scale = Math.min(1, 1000 / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(bitmap.width * scale));
    canvas.height = Math.max(1, Math.round(bitmap.height * scale));
    const context = canvas.getContext('2d');
    if (!context)
      throw new Error('Unable to prepare this photo.');
    context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.65);
  }
  finally {
    bitmap.close();
  }
}
export const mockApi: ApiService = {
  async getLocations() { await wait(); return clone(DEMO_AREAS); },
  async getTrend(id, range) { await wait(); return demoTrend(id, range); },
  async compare(a, b) { await wait(); return clone(DEMO_AREAS.filter((area) => area.id === a || area.id === b)); },
  async login(rawEmail, password) {
    await wait(450);
    const email = rawEmail.trim().toLowerCase();
    const builtin = BUILTIN_USERS.find((user) => user.email === email);
    if (builtin) {
      const expected = builtin.role === 'admin' ? DEMO_CREDENTIALS.admin.password : DEMO_CREDENTIALS.user.password;
      if (password !== expected)
        throw new Error('Email or password is incorrect. Try one of the demo accounts below.');
      return beginSession(builtin);
    }
    const hash = await hashPassword(email, password);
    const account = readStored<DemoAccount[]>('demo-accounts', [], true).find((item) => item.user.email === email && item.passwordHash === hash);
    if (!account)
      throw new Error('Email or password is incorrect. Demo registrations last for this browser tab only.');
    return beginSession(account.user);
  },
  async register(name, rawEmail, password) {
    await wait(450);
    const email = rawEmail.trim().toLowerCase();
    if (name.trim().length < 2 || !validEmail(email) || password.length < 8)
      throw new Error('Enter a name, valid email, and at least 8 password characters.');
    const accounts = readStored<DemoAccount[]>('demo-accounts', [], true);
    if ([...BUILTIN_USERS, ...accounts.map((account) => account.user)].some((user) => user.email === email))
      throw new Error('This email already has a demo account. Please sign in instead.');
    const user: User = { id: crypto.randomUUID(), name: name.trim(), email, role: 'user' };
    accounts.push({ user, passwordHash: await hashPassword(email, password) });
    writeStored('demo-accounts', accounts, true);
    return beginSession(user);
  },
  async refresh() { await wait(90); const user = currentUser(); return user ? beginSession(user) : null; },
  async logout() { removeStored('demo-session', true); },
  async getProfile() { await wait(); return readStored<HealthProfile | null>(`profile:${requireUser().id}`, null, true); },
  async saveProfile(profile) { await wait(); writeStored(`profile:${requireUser().id}`, profile, true); notifyDataChanged(); return clone(profile); },
  async deleteProfile() { await wait(); removeStored(`profile:${requireUser().id}`, true); notifyDataChanged(); },
  async getAdvisory(id, profile) {
    await wait();
    const reading = DEMO_AREAS.find((area) => area.id === id)?.reading;
    if (!reading)
      throw new Error('No direct reading is available for this area. Choose a nearby station.');
    return makeDemoAdvisory(reading.aqi, profile);
  },
  async getFavorites() { await wait(); return readStored<string[]>(`favorites:${requireUser().id}`, []); },
  async setFavorite(id, saved) {
    await wait(150);
    const key = `favorites:${requireUser().id}`;
    const favorites = readStored<string[]>(key, []);
    const next = saved ? [...new Set([...favorites, id])] : favorites.filter((item) => item !== id);
    writeStored(key, next);
    notifyDataChanged();
    return next;
  },
  async getAlerts() { await wait(); return readStored<AlertRule[]>(`alerts:${requireUser().id}`, []); },
  async saveAlert(alert) {
    await wait();
    if (!validThreshold(alert.threshold))
      throw new Error('AQI threshold must be a whole number between 1 and 500.');
    const id = requireUser().id;
    if (!readStored<string[]>(`favorites:${id}`, []).includes(alert.areaId))
      throw new Error('Save this location before creating an alert.');
    const key = `alerts:${id}`;
    const next = [...readStored<AlertRule[]>(key, []), { ...alert, id: crypto.randomUUID() }];
    writeStored(key, next);
    notifyDataChanged();
    return next;
  },
  async toggleAlert(id) {
    await wait(120);
    const key = `alerts:${requireUser().id}`;
    const next = readStored<AlertRule[]>(key, []).map((alert) => alert.id === id ? { ...alert, enabled: !alert.enabled } : alert);
    writeStored(key, next);
    notifyDataChanged();
    return next;
  },
  async deleteAlert(id) {
    await wait(120);
    const key = `alerts:${requireUser().id}`;
    const next = readStored<AlertRule[]>(key, []).filter((alert) => alert.id !== id);
    writeStored(key, next);
    notifyDataChanged();
    return next;
  },
  async getReports() { await wait(); return clone(readReports()); },
  async submitReport(form, progress) {
    progress(5);
    await wait(150);
    const category = String(form.get('category')) as PollutionReport['category'];
    const description = String(form.get('description') ?? '').trim();
    const areaId = String(form.get('areaId'));
    const area = DEMO_AREAS.find((item) => item.id === areaId);
    const latitude = Number(form.get('latitude'));
    const longitude = Number(form.get('longitude'));
    if (!['dust', 'burning', 'traffic', 'industrial', 'other'].includes(category) || description.length < 15 || description.length > 1500 || !area || !isInValley(latitude, longitude))
      throw new Error('Check the report category, description, and valley location.');
    let photo: string | undefined;
    const file = form.get('photo');
    if (file instanceof File && file.size > 0) {
      if (validatePhoto(file))
        throw new Error('Choose a JPEG, PNG, or WebP photo under 5 MB.');
      try {
        photo = await photoDataUrl(file);
      }
      catch {
        throw new Error('This photo could not be read. Please choose another image.');
      }
    }
    progress(55);
    await wait(250);
    const anonymous = form.get('anonymous') !== 'false' || !currentUser();
    const report: PollutionReport = {
      id: `AH-${Date.now().toString(36).toUpperCase()}`, category, description, areaId, latitude, longitude,
      anonymous, author: anonymous ? 'Anonymous' : requireUser().name, status: 'unverified',
      createdAt: new Date().toISOString(), photo, isDemo: true,
    };
    persistReports([report, ...readReports()]);
    progress(100);
    return clone(report);
  },
  async moderateReport(id: string, status: ReportStatus) {
    requireAdmin();
    await wait(200);
    if (!['verified', 'rejected', 'flagged', 'unverified'].includes(status))
      throw new Error('Invalid moderation status.');
    const reports = readReports();
    const found = reports.find((report) => report.id === id);
    if (!found)
      throw new Error('This report no longer exists. Refresh the queue.');
    const next = { ...found, status };
    persistReports(reports.map((report) => report.id === id ? next : report));
    return clone(next);
  },
  async getAdminStats() {
    requireAdmin();
    await wait();
    const reports = readReports();
    return { users: BUILTIN_USERS.length + readStored<DemoAccount[]>('demo-accounts', [], true).length, reports: reports.length, pending: reports.filter((report) => report.status === 'unverified').length, flagged: reports.filter((report) => report.status === 'flagged').length };
  },
};
