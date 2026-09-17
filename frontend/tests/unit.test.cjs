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
