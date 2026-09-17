import { test, expect, type Page } from '@playwright/test';

async function demoLogin(page: Page, role: 'user' | 'admin' = 'user', next = '/dashboard') {
  await page.goto(`/login?next=${encodeURIComponent(next)}`);
  await page.getByRole('button', {
    name: role === 'admin' ? 'Explore as a demo moderator' : 'Explore as a demo user',
    exact: true,
  }).click();
  await expect(page).toHaveURL(new RegExp(`${next}$`));
}

test.beforeEach(async ({ page }) => {
  // Repeatable tests: exercise the explicit map-network-failure state, not a third-party SLA.
  await page.route('**/*.basemaps.cartocdn.com/**', (route) => route.abort());
  await page.route('https://fonts.googleapis.com/**', (route) => route.abort());
  await page.route('https://fonts.gstatic.com/**', (route) => route.abort());
});

for (const route of ['/', '/map', '/areas/patan', '/areas/sankhu', '/compare', '/advisory', '/community', '/awareness', '/design-system']) {
  test(`public route ${route} renders without horizontal overflow`, async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto(route);
    await expect(page.locator('main')).toBeVisible();
    await expect(page.locator('main h1')).toBeVisible();
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBe(true);
    expect(errors).toEqual([]);
  });
}

test('guest routes redirect; ordinary users cannot moderate', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page).toHaveURL(/\/login\?next=/);
  await demoLogin(page);
  await page.goto('/admin');
  await expect(page.getByRole('button', { name: 'Verify', exact: true })).toHaveCount(0);
  await expect(page.locator('main')).toContainText('admin role');
});

test('location, trend range, accessible data table and CSV export', async ({ page }) => {
  await page.goto('/areas/patan');
  await page.getByRole('button', { name: '7 days', exact: true }).click();
  await expect(page.getByRole('button', { name: '7 days', exact: true })).toHaveAttribute('aria-pressed', 'true');
  await page.getByRole('button', { name: 'Data table', exact: true }).click();
  await expect(page.locator('.chart-data tbody tr')).toHaveCount(7);
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download CSV', exact: true }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain('patan');
});

test('stationless area has an explicit nearest-station state', async ({ page }) => {
  await page.goto('/areas/sankhu');
  await expect(page.locator('main')).toContainText('No direct data');
  await expect(page.locator('main')).toContainText('Nearest station');
});

test('same location has a higher illustrative risk for child-with-asthma example', async ({ page }) => {
  await page.goto('/advisory');
  await page.locator('.profile-example-list button').nth(1).click();
  await expect(page.locator('.advisory-panel')).toContainText('Lower demo risk');
  await page.locator('.profile-example-list button').nth(2).click();
  await expect(page.locator('.advisory-panel')).toContainText('Higher demo risk');
  await expect(page.locator('.advisory-panel')).toContainText('asthma');
  await expect(page.locator('.advisory-panel')).toContainText('not medical advice');
});

test('saved locations, optional profile, and alert configuration', async ({ page }) => {
  await demoLogin(page, 'user', '/areas/patan');
  await page.getByRole('button', { name: 'Save location', exact: true }).first().click();
  await expect(page.getByRole('button', { name: 'Remove saved location', exact: true }).first()).toBeVisible();
  await page.goto('/profile');
  await page.locator('input[name="ageGroup"][value="child"]').check();
  await page.locator('.condition-choice input').first().check();
  await page.getByRole('button', { name: 'Save profile', exact: true }).click();
  await expect(page.locator('.toast-stack')).toContainText('Your demo profile has been saved.');
  await page.reload();
  await expect(page.locator('input[name="ageGroup"][value="child"]')).toBeChecked();
  await page.goto('/dashboard');
  await expect(page.locator('.saved-grid')).toContainText('Patan');
  await page.getByRole('button', { name: 'Create an alert', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Create an alert' });
  await dialog.getByLabel('US AQI threshold').fill('100');
  await dialog.getByRole('button', { name: 'Create an alert', exact: true }).click();
  await expect(page.getByRole('switch').first()).toHaveAttribute('aria-checked', 'true');
  await page.getByRole('switch').first().click();
  await expect(page.getByRole('switch').first()).toHaveAttribute('aria-checked', 'false');
});

test('anonymous reporting validates uploads and creates an unverified report', async ({ page }) => {
  await page.goto('/community?compose=1');
  await page.getByRole('radio', { name: 'Road & construction dust' }).check();
  await page.getByLabel('Describe the concern').fill('Demo observation: dust beside a construction site near the selected location.');
  await page.locator('input[type="file"]').setInputFiles({ name: 'unsafe.txt', mimeType: 'text/plain', buffer: Buffer.from('not an image') });
  await expect(page.locator('.field-error')).toBeVisible();
  await page.getByRole('button', { name: 'Dismiss', exact: true }).click();
  await page.getByRole('button', { name: 'Submit demo report', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Thanks for adding your perspective.' })).toBeVisible();
  await expect(page.locator('.report-success')).toContainText('Unverified');
  await page.getByRole('button', { name: 'View reports', exact: true }).click();
  await expect(page.locator('.reports-grid')).toContainText('Demo observation: dust');
});

test('moderator updates report status and the queue', async ({ page }) => {
  await demoLogin(page, 'admin', '/admin');
  const initial = await page.locator('.moderation-row').count();
  expect(initial).toBeGreaterThan(0);
  await page.getByRole('button', { name: 'Verify', exact: true }).first().click();
  await expect(page.locator('.moderation-row')).toHaveCount(initial - 1);
  await page.getByRole('button', { name: 'Verified', exact: true }).click();
  await expect(page.locator('.moderation-row')).not.toHaveCount(0);
});

test('modal keyboard dismissal and mobile navigation', async ({ page, isMobile }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'About this demo', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'About this demo' })).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog', { name: 'About this demo' })).not.toBeVisible();
  if (isMobile) {
    await page.getByRole('button', { name: 'Navigation menu' }).click();
    await page.getByRole('navigation', { name: 'Mobile navigation' }).getByRole('link', { name: 'Air map', exact: true }).click();
    await expect(page).toHaveURL(/\/map$/);
  }
});
