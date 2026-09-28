/**
 * Translation layer between the backend's wire format (snake_case, integer
 * ids, generated in types/api.generated.ts) and the frontend's own domain
 * types (types/api.ts). Pure functions only -- no network, no globals -- so
 * they are unit-tested (tests/unit.test.cjs).
 *
 * Because the backend shapes come from the generated file, a backend contract
 * change that breaks a mapper fails `npm run typecheck` instead of failing at
 * runtime. Re-run `npm run types:generate` whenever the API changes.
 */
import type { components } from '../types/api.generated';
import type {
  AdminStats, Advisory, AlertRule, Area, District, HealthFlag, HealthProfile, PollutionReport,
  Pollutant, Reading, Reliability, ReportCategory, ReportStatus, Session, TrendPoint, User,
} from '../types/api';
import { distanceKm } from '../utils/geo';

type Schemas = components['schemas'];
export type ApiReading = Schemas['ReadingOut'];
export type ApiLocation = Schemas['LocationOut'];
export type ApiProfile = Schemas['ProfileOut'];
export type ApiProfileIn = Schemas['ProfileIn'];
export type ApiAdvisory = Schemas['AdvisoryOut'];
export type ApiAlert = Schemas['AlertOut'];
export type ApiReport = Schemas['ReportOut'] | Schemas['AdminReportOut'];
export type ApiUser = Schemas['UserOut'];
export type ApiTokenPair = Schemas['TokenPair'];
export type ApiStats = Schemas['StatsOut'];

// ---------- readings & areas ------------------------------------------------

const POLLUTANTS: Record<string, Pollutant> = {
  pm25: 'PM2.5', 'pm2.5': 'PM2.5', pm10: 'PM10', o3: 'O3', no2: 'NO2', so2: 'SO2', co: 'CO',
};

export function toPollutant(name: string | null | undefined): Pollutant | null {
  return name ? POLLUTANTS[name.toLowerCase()] ?? null : null;
}

const RELIABILITIES: Reliability[] = ['official', 'sensor', 'community', 'modelled'];

export function toReliability(status: string): Reliability {
  // An unknown future value is shown as the least-authoritative label rather
  // than being presented as "official".
  return (RELIABILITIES as string[]).includes(status) ? (status as Reliability) : 'community';
}

const MS_TO_KMH = 3.6;
const round1 = (value: number) => Math.round(value * 10) / 10;

/**
 * A reading with no AQI (a source that only gave raw concentrations) is
 * returned as null: the UI then shows the honest "no direct data" state
 * instead of an invented number.
 */
export function toReading(reading: ApiReading | null | undefined): Reading | null {
  if (!reading || reading.aqi === null || reading.aqi === undefined)
    return null;
  const pollutants: Reading['pollutants'] = {};
  const raw: [Pollutant, number | null][] = [
    ['PM2.5', reading.pm25], ['PM10', reading.pm10], ['O3', reading.o3],
    ['NO2', reading.no2], ['SO2', reading.so2], ['CO', reading.co],
  ];
  for (const [name, value] of raw)
    if (value !== null && value !== undefined)
      pollutants[name] = value;
  return {
    aqi: reading.aqi,
    mainPollutant: toPollutant(reading.main_pollutant),
    pollutants,
    source: reading.source,
    reliability: toReliability(reading.reliability_status),
    observedAt: reading.recorded_at,
    weather: {
      temperature: reading.temperature ?? null,
      humidity: reading.humidity ?? null,
      // Source APIs report m/s; the UI shows km/h.
      windSpeed: reading.wind === null || reading.wind === undefined ? null : round1(reading.wind * MS_TO_KMH),
      windDirection: null,
    },
    isDemo: false,
  };
}

/** "Pulchowk, Kathmandu, Nepal" -> "Pulchowk". */
export function cleanName(areaName: string): string {
  const first = areaName.split(',')[0]?.trim();
  return first || areaName;
}

const DISTRICT_KEYWORDS: [RegExp, District][] = [
  [/bhaktapur|thimi|changu/i, 'Bhaktapur'],
  [/lalitpur|patan|godawari|imadol/i, 'Lalitpur'],
  [/kavre|dhulikhel|banepa/i, 'Other'],
  [/kathmandu|ktm|kirtipur|kritipur/i, 'Kathmandu'],
];
const DISTRICT_CENTROIDS: [District, number, number][] = [
  ['Kathmandu', 27.71, 85.32], ['Lalitpur', 27.66, 85.32], ['Bhaktapur', 27.67, 85.43],
];

/**
 * The backend has no district field. Use the station's own name when it says
 * where it is; otherwise the nearest district centre, but never claim one of
 * the three valley districts for a point far outside the valley.
 */
export function districtFor(areaName: string, latitude: number, longitude: number): District {
  for (const [pattern, district] of DISTRICT_KEYWORDS)
    if (pattern.test(areaName))
      return district;
  const here = { latitude, longitude };
  const [nearest, distance] = DISTRICT_CENTROIDS
    .map(([district, lat, lng]) => [district, distanceKm(here, { latitude: lat, longitude: lng })] as const)
    .sort((a, b) => a[1] - b[1])[0];
  return distance <= 15 ? nearest : 'Other';
}

export function toArea(location: ApiLocation, featured = false): Area {
  const name = cleanName(location.area_name);
  return {
    id: String(location.id),
    name,
    // The backend holds no Nepali names; show the same name rather than
    // inventing a transliteration.
    nameNe: name,
    district: districtFor(location.area_name, location.latitude, location.longitude),
    latitude: location.latitude,
    longitude: location.longitude,
    reading: toReading(location.latest_reading),
    description: '',
    featured,
  };
}

/** The first few stations with a usable reading get the large map bubbles. */
export function toAreas(locations: ApiLocation[], featuredCount = 3): Area[] {
  let remaining = featuredCount;
  return locations.map((location) => {
    const area = toArea(location);
    if (area.reading && remaining > 0) {
      remaining -= 1;
      area.featured = true;
    }
    return area;
  });
}

export function toTrendPoint(reading: ApiReading): TrendPoint {
  return { time: reading.recorded_at, aqi: reading.aqi ?? null };
}

// ---------- users, profile ---------------------------------------------------

export function toUser(user: ApiUser): User {
  return { id: String(user.id), name: user.full_name, email: user.email, role: user.role === 'admin' ? 'admin' : 'user' };
}

export function toSession(pair: ApiTokenPair): Session {
  return { user: toUser(pair.user), accessToken: pair.access_token };
}

const CONDITION_FIELDS: [HealthFlag, 'asthma' | 'respiratory_condition' | 'heart_condition' | 'pregnancy_status' | 'outdoor_worker'][] = [
  ['asthma', 'asthma'], ['respiratory', 'respiratory_condition'], ['heart', 'heart_condition'],
  ['pregnancy', 'pregnancy_status'], ['outdoorWorker', 'outdoor_worker'],
];

export function toApiProfile(profile: HealthProfile): ApiProfileIn {
  const has = (flag: HealthFlag) => profile.conditions.includes(flag);
  return {
    age_group: profile.ageGroup === '' ? null : profile.ageGroup === 'older' ? 'elderly' : profile.ageGroup,
    asthma: has('asthma'),
    respiratory_condition: has('respiratory'),
    heart_condition: has('heart'),
    pregnancy_status: has('pregnancy'),
    outdoor_worker: has('outdoorWorker'),
    activity_level: profile.activityLevel === '' ? null : profile.activityLevel,
  };
}

export function toHealthProfile(profile: ApiProfile, preferredLanguage: 'en' | 'ne'): HealthProfile {
  return {
    ageGroup: profile.age_group === 'elderly' ? 'older' : profile.age_group ?? '',
    conditions: CONDITION_FIELDS.filter(([, field]) => profile[field] === true).map(([flag]) => flag),
    activityLevel: profile.activity_level ?? '',
    preferredLanguage,
  };
}

// ---------- advisory ---------------------------------------------------------

/** The backend scores five levels; the UI styles three. The recommendation
 *  text and reasons always come through unchanged, so nothing is lost. */
const LEVEL_MAP: Record<string, Advisory['level']> = {
  low: 'low', moderate: 'elevated', high: 'high', very_high: 'high', severe: 'high',
};

export function toAdvisory(advisory: ApiAdvisory): Advisory {
  return {
    level: LEVEL_MAP[advisory.risk_level] ?? 'high',
    recommendationKey: `recommend_${LEVEL_MAP[advisory.risk_level] ?? 'high'}`,
    recommendation: advisory.recommendation,
    reasons: advisory.reasons.map((reason) => ({ key: reason.code, message: reason.message })),
    disclaimer: advisory.disclaimer,
    aqi: advisory.aqi,
    personalized: advisory.personalized,
    isDemo: false,
  };
}

// ---------- alerts -----------------------------------------------------------

export function toAlert(alert: ApiAlert): AlertRule {
  return {
    id: String(alert.id),
    areaId: String(alert.location_id),
    threshold: alert.aqi_threshold,
    channel: alert.notification_type === 'email' ? 'email' : 'in-app',
    enabled: alert.active,
  };
}

// ---------- reports ----------------------------------------------------------

// Frontend category <-> backend category.
const CATEGORY_TO_API: Record<ReportCategory, string> = {
  dust: 'dust', burning: 'waste_burning', traffic: 'vehicle_smoke', industrial: 'industrial', other: 'other',
};
const CATEGORY_FROM_API = Object.fromEntries(Object.entries(CATEGORY_TO_API).map(([ui, api]) => [api, ui])) as Record<string, ReportCategory>;

export const toApiCategory = (category: ReportCategory): string => CATEGORY_TO_API[category] ?? 'other';
export const fromApiCategory = (category: string): ReportCategory => CATEGORY_FROM_API[category] ?? 'other';

const STATUSES: ReportStatus[] = ['unverified', 'verified', 'rejected', 'flagged'];

/**
 * Public report lists never say who submitted a report, so they are always
 * shown as anonymous. Moderators also get `user_id` (null = anonymous).
 */
export function toReport(report: ApiReport, apiBaseUrl: string): PollutionReport {
  const submitter = 'user_id' in report ? report.user_id : null;
  const status = report.verification_status as ReportStatus;
  return {
    id: String(report.id),
    category: fromApiCategory(report.category),
    description: report.description ?? '',
    areaId: String(report.location_id),
    latitude: report.latitude,
    longitude: report.longitude,
    anonymous: submitter === null,
    author: submitter === null ? 'Anonymous' : `Member #${submitter}`,
    status: STATUSES.includes(status) ? status : 'unverified',
    createdAt: report.created_at,
    photo: report.image_url ? `${apiBaseUrl.replace(/\/$/, '')}${report.image_url}` : undefined,
    isDemo: false,
  };
}

export function toStats(stats: ApiStats): AdminStats {
  return { users: stats.users, reports: stats.reports, pending: stats.pending, flagged: stats.flagged };
}
