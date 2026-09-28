const { test, beforeEach } = require('node:test');
const assert = require('node:assert/strict');
const { AQI_CATEGORIES, getAqiCategory, clamp } = require('../.test-build/utils/aqi.js');
const { distanceKm, isInValley, nearestStation } = require('../.test-build/utils/geo.js');
const { makeDemoAdvisory } = require('../.test-build/utils/advisory.js');
const { validatePhoto, validEmail, validThreshold, MAX_PHOTO_BYTES } = require('../.test-build/utils/validation.js');
const { escapeHtml, csvCell, formatDate, formatTime } = require('../.test-build/utils/format.js');
const { DEMO_AREAS, demoTrend, demoForecast } = require('../.test-build/services/fixtures.js');
const { mockApi, DEMO_CREDENTIALS } = require('../.test-build/services/mockApi.js');
const { readStored, writeStored } = require('../.test-build/services/storage.js');

class MemoryStorage {
  values = new Map();
  getItem(key) { return this.values.get(key) ?? null; }
  setItem(key, value) { this.values.set(key, String(value)); }
  removeItem(key) { this.values.delete(key); }
  clear() { this.values.clear(); }
}
global.localStorage = new MemoryStorage();
global.sessionStorage = new MemoryStorage();
global.window = new EventTarget();
beforeEach(() => { localStorage.clear(); sessionStorage.clear(); });

for (const [value, expected] of [
  [0, 'good'], [50, 'good'], [51, 'moderate'], [100, 'moderate'],
  [101, 'sensitive'], [150, 'sensitive'], [151, 'unhealthy'], [200, 'unhealthy'],
  [201, 'veryUnhealthy'], [300, 'veryUnhealthy'], [301, 'hazardous'],
  [500, 'hazardous'], [800, 'hazardous'], [50.49, 'good'], [50.5, 'moderate'],
]) test(`AQI ${value} is ${expected}`, () => assert.equal(getAqiCategory(value)?.key, expected));
for (const value of [null, undefined, -1, NaN, Infinity]) {
  test(`invalid AQI ${value} produces no invented category`, () => assert.equal(getAqiCategory(value), null));
}
test('the full six-category palette is retained with distinct symbols', () => {
  assert.equal(AQI_CATEGORIES.length, 6);
  assert.equal(new Set(AQI_CATEGORIES.map((category) => category.symbol)).size, 6);
});
function luminance(hex) {
  const channels = hex.slice(1).match(/../g).map((channel) => {
    const value = parseInt(channel, 16) / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}
for (const category of AQI_CATEGORIES) test(`${category.key} badge text reaches a 4.5:1 contrast ratio`, () => {
  const ink = luminance(category.ink), background = luminance(category.background);
  const ratio = (Math.max(ink, background) + 0.05) / (Math.min(ink, background) + 0.05);
  assert.ok(ratio >= 4.5, `${ratio.toFixed(2)}:1 is insufficient`);
});
test('gauge values are clamped without changing the AQI label', () => {
  assert.equal(clamp(800, 0, 500), 500); assert.equal(clamp(-2, 0, 500), 0);
});
test('all sample neighborhoods are inside the valley bounds', () => {
  assert.ok(DEMO_AREAS.every((area) => isInValley(area.latitude, area.longitude)));
});
test('outside-valley and invalid coordinates are rejected', () => {
  assert.equal(isInValley(40.71, -74), false); assert.equal(isInValley(NaN, 85.3), false);
});
test('Haversine distance is zero at the same point and symmetric', () => {
  const [a, b] = DEMO_AREAS;
  assert.equal(distanceKm(a, a), 0);
  assert.ok(Math.abs(distanceKm(a, b) - distanceKm(b, a)) < 1e-9);
  assert.ok(distanceKm(a, b) > 3 && distanceKm(a, b) < 5);
});
test('stationless places use nearest context without changing their local reading', () => {
  const area = DEMO_AREAS.find((item) => item.id === 'sankhu');
  const nearest = nearestStation(area, DEMO_AREAS);
  assert.equal(area.reading, null); assert.ok(nearest.area.reading); assert.ok(nearest.distance > 0);
});
test('no available stations means no nearest-station result', () => {
  assert.equal(nearestStation(DEMO_AREAS[0], DEMO_AREAS.filter((area) => !area.reading)), null);
});
test('all seeded readings and report-like source assignments are explicitly fictional', () => {
  for (const area of DEMO_AREAS.filter((item) => item.reading)) {
    assert.equal(area.reading.isDemo, true); assert.match(area.reading.source, /fictional/);
  }
});
for (const [range, count] of [['24h', 24], ['7d', 7], ['30d', 30]]) test(`${range} trend contains ${count} ordered samples and a visible gap`, () => {
  const trend = demoTrend('ratnapark', range);
  assert.equal(trend.length, count); assert.ok(trend.some((point) => point.aqi === null));
  assert.ok(trend.every((point, index) => !index || point.time > trend[index - 1].time));
});
test('missing readings never receive invented historical or forecast values', () => {
  assert.deepEqual(demoTrend('sankhu', '7d'), []); assert.deepEqual(demoForecast('sankhu'), []);
});
test('projection points have forecast values, not observed values', () => {
  assert.ok(demoForecast('patan').every((point) => point.aqi === null && typeof point.forecast === 'number'));
});
test('a child with asthma has higher demo risk than a healthy adult at the same AQI', () => {
  const base = { ageGroup: 'adult', conditions: [], activityLevel: 'moderate', preferredLanguage: 'en' };
  const adult = makeDemoAdvisory(78, base);
  const child = makeDemoAdvisory(78, { ...base, ageGroup: 'child', conditions: ['asthma'] });
  assert.equal(adult.level, 'low'); assert.equal(child.level, 'high');
  assert.equal(adult.aqi, child.aqi); assert.ok(child.reasons.some((reason) => reason.key === 'reason_asthma'));
});
test('general advice explicitly says no profile is applied', () => {
  const result = makeDemoAdvisory(42, null);
  assert.equal(result.personalized, false); assert.equal(result.isDemo, true);
  assert.ok(result.reasons.some((reason) => reason.key === 'reasonGeneric'));
});
test('image validation rejects executable formats, oversize images and empty files', () => {
  assert.equal(validatePhoto({ size: 1, type: 'image/svg+xml' }), 'photoType');
  assert.equal(validatePhoto({ size: MAX_PHOTO_BYTES + 1, type: 'image/png' }), 'photoSize');
  assert.equal(validatePhoto({ size: 0, type: 'image/jpeg' }), 'photoEmpty');
  assert.equal(validatePhoto({ size: MAX_PHOTO_BYTES, type: 'image/webp' }), null);
});
test('email and integer AQI thresholds are validated', () => {
  assert.equal(validEmail('demo@example.com'), true); assert.equal(validEmail('bad@'), false);
  assert.equal(validThreshold(1), true); assert.equal(validThreshold(500), true);
  for (const value of [0, 501, 22.5, NaN]) assert.equal(validThreshold(value), false);
});
test('map label content is HTML escaped', () => {
  assert.equal(escapeHtml('<img onerror="x">&'), '&lt;img onerror=&quot;x&quot;&gt;&amp;');
});
test('CSV export quotes fields and neutralizes spreadsheet formulas', () => {
  assert.equal(csvCell('a"b'), '"a""b"');
  assert.ok(csvCell('=HYPERLINK("bad")').startsWith('"\''));
  assert.equal(csvCell(null), '""');
});
test('times use Nepal time rather than the host machine timezone', () => {
  assert.equal(formatTime('2026-09-14T04:15:00Z'), '10:00');
  assert.equal(formatDate('invalid'), '\u2014');
});
test('malformed JSON is safely replaced by the supplied fallback', () => {
  localStorage.setItem('aero-health-v2:broken', '{bad');
  assert.deepEqual(readStored('broken', []), []);
});
test('storage quota errors are surfaced rather than pretending to save', () => {
  const original = localStorage.setItem;
  localStorage.setItem = () => { throw new Error('quota'); };
  assert.throws(() => writeStored('anything', 'value'), /unavailable or full/);
  localStorage.setItem = original;
});

test('guest accounts cannot read private profile data or administer reports', async () => {
  await assert.rejects(mockApi.getProfile(), /sign in/);
  await assert.rejects(mockApi.moderateReport('AH-1042', 'verified'), /sign in/);
});
test('bad credentials are rejected', async () => {
  await assert.rejects(mockApi.login(DEMO_CREDENTIALS.user.email, 'wrong'), /incorrect/);
});
test('registration signs in, rejects duplicates, and does not store raw passwords', async () => {
  const result = await mockApi.register('Test Member', 'test@example.com', 'FakePassword123!');
  assert.equal(result.user.role, 'user'); assert.match(result.accessToken, /^demo-only-/);
  assert.ok(!sessionStorage.getItem('aero-health-v2:demo-accounts').includes('FakePassword123!'));
  await assert.rejects(mockApi.register('Other User', 'test@example.com', 'AnotherFake123!'), /already/);
  await mockApi.logout(); assert.equal(await mockApi.refresh(), null);
  assert.equal((await mockApi.login('test@example.com', 'FakePassword123!')).user.id, result.user.id);
});
test('profile, favorites, alerts and account isolation work together', async () => {
  await mockApi.login(DEMO_CREDENTIALS.user.email, DEMO_CREDENTIALS.user.password);
  assert.equal(await mockApi.getProfile(), null);
  const profile = { ageGroup: 'child', conditions: ['asthma'], activityLevel: '', preferredLanguage: 'en' };
  await mockApi.saveProfile(profile); assert.deepEqual(await mockApi.getProfile(), profile);
  await mockApi.setFavorite('ratnapark', true); await mockApi.setFavorite('ratnapark', true);
  assert.deepEqual(await mockApi.getFavorites(), ['ratnapark']);
  const rules = await mockApi.saveAlert({ areaId: 'ratnapark', threshold: 75, channel: 'in-app', enabled: true });
  assert.equal(rules.length, 1); assert.equal((await mockApi.toggleAlert(rules[0].id))[0].enabled, false);
  assert.deepEqual(await mockApi.deleteAlert(rules[0].id), []);
  await assert.rejects(mockApi.saveAlert({ areaId: 'patan', threshold: 100, channel: 'email', enabled: true }), /Save this location/);
  await mockApi.deleteProfile(); assert.equal(await mockApi.getProfile(), null);
  await mockApi.login(DEMO_CREDENTIALS.admin.email, DEMO_CREDENTIALS.admin.password);
  assert.deepEqual(await mockApi.getFavorites(), []);
});
function reportData(description = 'A fictional observation of dust for the test suite.') {
  const data = new FormData();
  for (const [key, value] of Object.entries({ category: 'dust', description, areaId: 'ratnapark', latitude: '27.7067', longitude: '85.3153', anonymous: 'true' })) data.set(key, value);
  return data;
}
test('anonymous report submission starts unverified, tracks progress, and rejects invalid input', async () => {
  const progress = [];
  const result = await mockApi.submitReport(reportData(), (value) => progress.push(value));
  assert.equal(result.status, 'unverified'); assert.equal(result.anonymous, true); assert.equal(result.isDemo, true);
  assert.equal(progress.at(-1), 100);
  assert.ok((await mockApi.getReports()).some((report) => report.id === result.id));
  await assert.rejects(mockApi.submitReport(reportData('short'), () => {}), /Check/);
  const invalid = reportData(); invalid.set('latitude', '99');
  await assert.rejects(mockApi.submitReport(invalid, () => {}), /Check/);
});
test('moderation requires the admin role and actually updates report status and stats', async () => {
  await mockApi.login(DEMO_CREDENTIALS.user.email, DEMO_CREDENTIALS.user.password);
  await assert.rejects(mockApi.moderateReport('AH-1042', 'verified'), /administrator/);
  await mockApi.login(DEMO_CREDENTIALS.admin.email, DEMO_CREDENTIALS.admin.password);
  const before = await mockApi.getAdminStats();
  const updated = await mockApi.moderateReport('AH-1042', 'verified');
  assert.equal(updated.status, 'verified');
  const after = await mockApi.getAdminStats(); assert.equal(after.pending, before.pending - 1);
  assert.equal((await mockApi.getReports()).find((report) => report.id === 'AH-1042').status, 'verified');
});

// ---------------------------------------------------------------------------
// Backend -> UI mappers (services/mappers.ts). Fixtures mirror real API output.
// ---------------------------------------------------------------------------
const M = require('../.test-build/services/mappers.js');

const apiReading = (over = {}) => ({
  id: 1, location_id: 2, aqi: 62, aqi_category: 'Moderate', main_pollutant: 'pm25',
  pm25: 18.4, pm10: null, o3: 21, no2: null, so2: null, co: null,
  temperature: 24.5, humidity: 61, wind: 2, pressure: 1010, owm_aqi_index: null,
  source: 'waqi', reliability_status: 'official',
  recorded_at: '2026-09-16T15:00:00Z', fetched_at: '2026-09-16T15:05:00Z', ...over,
});
const apiLocation = (over = {}) => ({
  id: 2, area_name: 'Pulchowk, Kathmandu, Nepal', ward: null, latitude: 27.68, longitude: 85.32,
  source_station_id: '9285', latest_reading: apiReading(), ...over,
});

test('a reading maps to the UI shape with honesty fields intact', () => {
  const reading = M.toReading(apiReading());
  assert.equal(reading.aqi, 62);
  assert.equal(reading.mainPollutant, 'PM2.5');
  assert.equal(reading.source, 'waqi');
  assert.equal(reading.reliability, 'official');
  assert.equal(reading.observedAt, '2026-09-16T15:00:00Z');
  assert.equal(reading.isDemo, false);
});
test('only pollutants the station actually measured are present', () => {
  const { pollutants } = M.toReading(apiReading());
  assert.deepEqual(pollutants, { 'PM2.5': 18.4, O3: 21 });
  assert.equal('PM10' in pollutants, false);
});
test('wind converts from m/s to km/h and missing weather stays null', () => {
  assert.equal(M.toReading(apiReading({ wind: 2 })).weather.windSpeed, 7.2);
  const w = M.toReading(apiReading({ wind: null, temperature: null, humidity: null })).weather;
  assert.deepEqual([w.windSpeed, w.temperature, w.humidity], [null, null, null]);
});
test('a reading without an AQI is null, never an invented number', () => {
  assert.equal(M.toReading(apiReading({ aqi: null, aqi_category: null })), null);
  assert.equal(M.toReading(null), null);
  assert.equal(M.toArea(apiLocation({ latest_reading: apiReading({ aqi: null }) })).reading, null);
});
test('an unrecognised pollutant or reliability is never promoted', () => {
  assert.equal(M.toReading(apiReading({ main_pollutant: 'mystery' })).mainPollutant, null);
  assert.equal(M.toReading(apiReading({ main_pollutant: null })).mainPollutant, null);
  assert.equal(M.toReliability('brand-new-status'), 'community');
  assert.equal(M.toReliability('sensor'), 'sensor');
  assert.equal(M.toReliability('modelled'), 'modelled');
});
test('locations map to areas with string ids and clean names', () => {
  const area = M.toArea(apiLocation());
  assert.equal(area.id, '2');
  assert.equal(area.name, 'Pulchowk');
  assert.equal(area.nameNe, 'Pulchowk');
  assert.equal(area.district, 'Kathmandu');
  assert.equal(area.latitude, 27.68);
  assert.equal(M.cleanName('TU Kritipur, Nepal'), 'TU Kritipur');
  assert.equal(M.cleanName('US Diplomatic Post: Embassy Kathmandu'), 'US Diplomatic Post: Embassy Kathmandu');
});
test('districts come from the name, then geography, and never over-claim', () => {
  assert.equal(M.districtFor('Birendra School, Bhaktapur, Nepal', 27.67, 85.41), 'Bhaktapur');
  assert.equal(M.districtFor('Dhulikhel, Kavre, Nepal', 27.61, 85.55), 'Other');
  assert.equal(M.districtFor('Khumaltar, Nepal', 27.6467, 85.3234), 'Lalitpur');
  assert.equal(M.districtFor('Somewhere far, Nepal', 28.4, 84.0), 'Other');
});
test('only the first few stations with data are featured', () => {
  const locations = [1, 2, 3, 4, 5].map((id) => apiLocation({ id, latest_reading: id === 1 ? null : apiReading({ location_id: id }) }));
  const areas = M.toAreas(locations, 3);
  assert.deepEqual(areas.map((area) => area.featured), [false, true, true, true, false]);
});
test('trend points keep gaps as null', () => {
  assert.deepEqual(M.toTrendPoint(apiReading({ aqi: null })), { time: '2026-09-16T15:00:00Z', aqi: null });
  assert.equal(M.toTrendPoint(apiReading({ aqi: 80 })).aqi, 80);
});
test('session and user mapping only ever yields user or admin', () => {
  const user = { id: 7, full_name: 'Sita', email: 's@x.com', role: 'user', preferred_language: 'en', created_at: 'x' };
  const session = M.toSession({ access_token: 'tok', refresh_token: 'r', token_type: 'bearer', user });
  assert.deepEqual(session, { user: { id: '7', name: 'Sita', email: 's@x.com', role: 'user' }, accessToken: 'tok' });
  assert.equal(M.toUser({ ...user, role: 'superuser' }).role, 'user');
  assert.equal(M.toUser({ ...user, role: 'admin' }).role, 'admin');
});
test('a health profile survives a UI -> API -> UI round trip', () => {
  const ui = { ageGroup: 'older', conditions: ['asthma', 'heart', 'outdoorWorker'], activityLevel: 'high', preferredLanguage: 'ne' };
  const wire = M.toApiProfile(ui);
  assert.deepEqual(wire, {
    age_group: 'elderly', asthma: true, respiratory_condition: false, heart_condition: true,
    pregnancy_status: false, outdoor_worker: true, activity_level: 'high',
  });
  assert.deepEqual(M.toHealthProfile({ id: 1, ...wire }, 'ne'), ui);
});
test('an empty profile maps to nulls, not empty strings', () => {
  const wire = M.toApiProfile({ ageGroup: '', conditions: [], activityLevel: '', preferredLanguage: 'en' });
  assert.equal(wire.age_group, null);
  assert.equal(wire.activity_level, null);
  assert.deepEqual(M.toHealthProfile({ id: 1, ...wire }, 'en'), { ageGroup: '', conditions: [], activityLevel: '', preferredLanguage: 'en' });
});
test('advisory keeps the backend reasons, text and disclaimer', () => {
  const advisory = M.toAdvisory({
    location_id: 2, aqi: 130, aqi_category: 'Unhealthy for Sensitive Groups', risk_level: 'very_high',
    recommendation: 'Avoid outdoor exertion.', disclaimer: 'Not medical advice.', personalized: true,
    reasons: [{ code: 'profile_asthma', message: 'Your profile includes asthma.' }],
    source: 'waqi', reliability_status: 'official', recorded_at: 'x',
  });
  assert.equal(advisory.level, 'high');
  assert.equal(advisory.recommendation, 'Avoid outdoor exertion.');
  assert.equal(advisory.disclaimer, 'Not medical advice.');
  assert.deepEqual(advisory.reasons, [{ key: 'profile_asthma', message: 'Your profile includes asthma.' }]);
  assert.equal(advisory.personalized, true);
});
test('a higher backend risk level never maps to a lower UI level', () => {
  const order = { low: 0, elevated: 1, high: 2 };
  const levels = ['low', 'moderate', 'high', 'very_high', 'severe'].map((risk_level) => order[M.toAdvisory({
    location_id: 1, aqi: 1, aqi_category: 'x', risk_level, recommendation: '', disclaimer: '', personalized: false, reasons: [],
    source: 's', reliability_status: 'official', recorded_at: 'x',
  }).level]);
  assert.deepEqual(levels, [...levels].sort());
});
test('alerts map ids, channel and enabled flag', () => {
  assert.deepEqual(M.toAlert({ id: 3, location_id: 2, aqi_threshold: 150, notification_type: 'email', active: false }),
    { id: '3', areaId: '2', threshold: 150, channel: 'email', enabled: false });
  assert.equal(M.toAlert({ id: 4, location_id: 2, aqi_threshold: 50, notification_type: 'in-app', active: true }).channel, 'in-app');
});
test('report categories translate both ways', () => {
  for (const ui of ['dust', 'burning', 'traffic', 'industrial', 'other']) assert.equal(M.fromApiCategory(M.toApiCategory(ui)), ui);
  assert.equal(M.toApiCategory('burning'), 'waste_burning');
  assert.equal(M.fromApiCategory('something_new'), 'other');
});
test('public reports are anonymous; moderator reports reveal only an id', () => {
  const base = { id: 9, location_id: 2, latitude: 27.7, longitude: 85.3, category: 'dust', description: 'Dusty road', severity: null, image_url: '/uploads/a.jpg', verification_status: 'unverified', created_at: '2026-09-16T00:00:00Z' };
  const pub = M.toReport(base, 'http://localhost:8000/');
  assert.equal(pub.anonymous, true);
  assert.equal(pub.author, 'Anonymous');
  assert.equal(pub.photo, 'http://localhost:8000/uploads/a.jpg');
  assert.equal(pub.areaId, '2');
  const named = M.toReport({ ...base, user_id: 5, image_url: null }, 'http://x');
  assert.equal(named.anonymous, false);
  assert.equal(named.author, 'Member #5');
  assert.equal(named.photo, undefined);
  assert.equal(M.toReport({ ...base, user_id: null }, 'http://x').anonymous, true);
  assert.equal(M.toReport({ ...base, verification_status: 'weird' }, 'http://x').status, 'unverified');
});
