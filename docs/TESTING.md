# Testing and validation record

## Passed during authoring

**54 tests of the actual project's own utilities and mock-service logic** passed using the installed Node/TypeScript runtime. These are the same tests included in `frontend/tests/unit.test.cjs`; they do not substitute third-party React, Leaflet, or Recharts packages.

Covered areas include all six AQI boundaries, invalid numeric inputs, badge contrast pairs, distance and nearest-station behavior, no-data fixtures, trend lengths and gaps, projection labeling, CSV formula escaping, HTML escaping, Nepal timestamps, photo/email/threshold validation, adult-versus-sensitive-profile reasoning, browser-storage failure behavior, guest/admin authorization simulation, login/register/duplicate registration, per-user profile/favorite/alert isolation, anonymous reporting and validation, and moderation statistics.

The source audit passed: 54 TypeScript modules, 260 local imports, and 384 literal English translation references at the time of authoring. Re-run `npm run lint` for current counts after edits. This audit checks syntax and references, not package-aware type correctness.

## Constrained source-render checks

The actual page components and own mock service were rendered in a local Chromium document with an available React 18 runtime and **temporary test-only substitutes** for routing, map, chart and i18n libraries, because the requested npm packages could not be downloaded. These substitutes are not in the delivered ZIP and must not be mistaken for the actual application dependencies.

35 page/flow observations at 375px and 1440px found no JavaScript page errors or horizontal document overflow in that source-render setup. The optional child/asthma profile save, user/admin role flow and moderation update were exercised there. Additional source-runtime checks verified valid photo preview/decoding and anonymous report submission, saving a location, and creating/toggling an alert. Layout screenshots were inspected, including overview, auth, advisory, profile, dashboard and report screens. This exercise caught a filter/legend overlap that was fixed.

A temporary approximate ambient-declaration check also found no internal source diagnostics. It is not equivalent to checking against the real packages and is not shipped as an application type declaration.

## Not verified in the authoring environment

Outbound DNS/package downloads were unavailable. Therefore:

- `npm install` could not complete, and no honest dependency lockfile could be produced.
- `npm run build` and the real dependency-aware `npm run typecheck` have not run successfully here.
- Actual React 19, React Router, React-Leaflet, Leaflet tile rendering, Recharts, Axios real-mode integration and full Vite bundling remain to be checked together.
- The included full Playwright suite has not been executed against installed production dependencies.
- No live backend, current AQI service, email/push service, complete WCAG audit or full native-language review was tested.

## Local verification

From `frontend/`:

```bash
npm install
npm run lint
npm test
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e
```

Inspect the Playwright HTML report with `npx playwright show-report`. Browser tests intentionally intercept the map/font requests, so they exercise graceful external-resource failure while running the **real installed** UI libraries. Separately open the application with working internet and inspect the real basemap and tooltips. Test geolocation only with consent.

After your first successful install, commit the resulting lockfile. The CI workflow uses `npm ci` when one is present and otherwise falls back to `npm install`. CI has not been run by this delivery.

## Manual acceptance checklist

Check 375px, tablet, laptop and wider desktop widths; real tiles; panning/zoom/recenter; reading selection; source/time display; a stationless area; all six AQI categories; chart gaps, table and CSV; compare/swap; registration/login/logout/refresh; keyboard-only navigation and dialogs; saved places; profile save/edit/clear; threshold validation/toggle/delete; report text, corrupt/oversize image, photo preview and upload failure; anonymous status; admin access restrictions and moderation persistence; reduced motion; high contrast; core Nepali and English fallback; and runtime console errors.

Do not base any medical, safety, or outdoor-activity decision on this demo's fictional readings or illustrative advisory output.
