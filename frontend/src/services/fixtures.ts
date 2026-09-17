import type { Area, PollutionReport, Reliability, Reading, TrendPoint, Range } from '../types/api';
// Coordinates locate real neighborhoods. Every measurement and provider assignment is fictional.
export const DEMO_OBSERVED_AT = '2026-09-14T04:15:00.000Z';
function reading(aqi: number, reliability: Reliability = 'modelled'): Reading {
  return {
    aqi, mainPollutant: 'PM2.5',
    pollutants: { 'PM2.5': Number((aqi * 0.318).toFixed(1)), PM10: Number((aqi * 0.61).toFixed(1)), O3: 21.4, NO2: 14.2, SO2: 4.8, CO: 0.6 },
    source: `Demo ${reliability} feed (fictional)`, reliability,
    observedAt: DEMO_OBSERVED_AT,
    weather: { temperature: 24, humidity: 62, windSpeed: 8, windDirection: 'SW' }, isDemo: true,
  };
}
export const DEMO_AREAS: Area[] = [
  { id: 'ratnapark', name: 'Ratnapark', nameNe: '\u0930\u0924\u094d\u0928\u092a\u093e\u0930\u094d\u0915', district: 'Kathmandu', latitude: 27.7067, longitude: 85.3153, reading: reading(78, 'official'), description: 'A central Kathmandu sample location, near the city core.', featured: true },
  { id: 'patan', name: 'Patan', nameNe: '\u092a\u093e\u091f\u0928', district: 'Lalitpur', latitude: 27.6727, longitude: 85.3253, reading: reading(42, 'official'), description: 'A sample location in the historic heart of Lalitpur.', featured: true },
  { id: 'bhaktapur', name: 'Bhaktapur', nameNe: '\u092d\u0915\u094d\u0924\u092a\u0941\u0930', district: 'Bhaktapur', latitude: 27.6710, longitude: 85.4298, reading: reading(156, 'community'), description: 'A sample location near the old city of Bhaktapur.', featured: true },
  { id: 'kirtipur', name: 'Kirtipur', nameNe: '\u0915\u0940\u0930\u094d\u0924\u093f\u092a\u0941\u0930', district: 'Kathmandu', latitude: 27.6784, longitude: 85.2779, reading: reading(38), description: 'Southwestern valley sample location.' },
  { id: 'kalanki', name: 'Kalanki', nameNe: '\u0915\u0932\u0902\u0915\u0940', district: 'Kathmandu', latitude: 27.6939, longitude: 85.2815, reading: reading(187, 'community'), description: 'Western Kathmandu sample location.' },
  { id: 'boudha', name: 'Boudha', nameNe: '\u092c\u094c\u0926\u094d\u0927', district: 'Kathmandu', latitude: 27.7214, longitude: 85.3620, reading: reading(124), description: 'Northeastern Kathmandu sample location.' },
  { id: 'balaju', name: 'Balaju', nameNe: '\u092c\u093e\u0932\u093e\u091c\u0941', district: 'Kathmandu', latitude: 27.7311, longitude: 85.3006, reading: reading(232), description: 'Northwestern Kathmandu sample location.' },
  { id: 'thimi', name: 'Madhyapur Thimi', nameNe: '\u092e\u0927\u094d\u092f\u092a\u0941\u0930 \u0920\u093f\u092e\u0940', district: 'Bhaktapur', latitude: 27.6805, longitude: 85.3878, reading: reading(93, 'community'), description: 'A sample location between Kathmandu and Bhaktapur.' },
  { id: 'godawari', name: 'Godawari', nameNe: '\u0917\u094b\u0926\u093e\u0935\u0930\u0940', district: 'Lalitpur', latitude: 27.5960, longitude: 85.3790, reading: reading(31), description: 'Southern valley sample location.' },
  { id: 'balkumari', name: 'Balkumari', nameNe: '\u092c\u093e\u0932\u0915\u0941\u092e\u093e\u0930\u0940', district: 'Lalitpur', latitude: 27.6702, longitude: 85.3426, reading: reading(315), description: 'A severe AQI example for testing the full category scale; not a real alert.' },
  { id: 'sankhu', name: 'Sankhu', nameNe: '\u0938\u093e\u0901\u0916\u0941', district: 'Kathmandu', latitude: 27.7290, longitude: 85.4640, reading: null, description: 'No direct reading in this demo. Nearby data is never presented as local measurement.' },
  { id: 'changu', name: 'Changunarayan', nameNe: '\u091a\u093e\u0901\u0917\u0941\u0928\u093e\u0930\u093e\u092f\u0923', district: 'Bhaktapur', latitude: 27.7165, longitude: 85.4306, reading: null, description: 'An example of an area without a direct station reading.' },
];
export function demoTrend(id: string, range: Range): TrendPoint[] {
  const baseline = DEMO_AREAS.find((area) => area.id === id)?.reading?.aqi;
  if (baseline === undefined)
    return [];
  const count = range === '24h' ? 24 : range === '7d' ? 7 : 30;
  const step = range === '24h' ? 3600000 : 86400000;
  const end = Date.parse(DEMO_OBSERVED_AT);
  return Array.from({ length: count }, (_, i) => ({
    time: new Date(end - (count - 1 - i) * step).toISOString(),
    aqi: i === Math.floor(count * 0.4) ? null : Math.max(8, Math.round(baseline + Math.sin(i * 0.84) * 12 + Math.cos(i * 0.43) * 9 - 8)),
  }));
}
export function demoForecast(id: string): TrendPoint[] {
  const baseline = DEMO_AREAS.find((area) => area.id === id)?.reading?.aqi;
  if (baseline === undefined)
    return [];
  const start = Date.parse(DEMO_OBSERVED_AT);
  return Array.from({ length: 12 }, (_, i) => ({ time: new Date(start + i * 3600000).toISOString(), aqi: null, forecast: Math.round(Math.max(8, baseline + Math.sin(i / 1.3) * 13 - i * 1.4)) }));
}
export const DEMO_REPORTS: PollutionReport[] = [
  { id: 'AH-1042', category: 'dust', description: 'Demo report: visible dust near road works. This is a fictional example for the moderation workflow.', areaId: 'kalanki', latitude: 27.6939, longitude: 85.2815, anonymous: true, author: 'Anonymous', status: 'unverified', createdAt: '2026-09-14T02:45:00Z', isDemo: true },
  { id: 'AH-1041', category: 'burning', description: 'Demo report: smoke observed beside an open plot. The location and incident are illustrative only.', areaId: 'thimi', latitude: 27.6805, longitude: 85.3878, anonymous: false, author: 'Aero community demo', status: 'unverified', createdAt: '2026-09-13T10:45:00Z', isDemo: true },
  { id: 'AH-1040', category: 'traffic', description: 'Demo report: idling vehicles during a busy period. Verified here means a demo moderation action, not an official finding.', areaId: 'ratnapark', latitude: 27.7067, longitude: 85.3153, anonymous: true, author: 'Anonymous', status: 'verified', createdAt: '2026-09-13T06:30:00Z', isDemo: true },
  { id: 'AH-1039', category: 'industrial', description: 'Demo report: a sample industrial-emission concern awaiting further review.', areaId: 'balkumari', latitude: 27.6702, longitude: 85.3426, anonymous: true, author: 'Anonymous', status: 'flagged', createdAt: '2026-09-12T05:00:00Z', isDemo: true },
];
