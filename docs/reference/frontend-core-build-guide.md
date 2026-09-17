# Aero Health — Frontend Core Build Guide (React + Vite)

A step-by-step path for the two frontend members to build smoothly:
- **M4 — Maps & Visualization** (map, area detail, charts, comparison)
- **M5 — User & Community** (auth, profile, dashboard, advisory display, reports, admin)

The first three phases are a **shared foundation** — build them together before the tracks split. After that, M4 (Track A) and M5 (Track B) run in parallel. Every step ends with a **✅ Done when** checkpoint.

**Stack:** TypeScript · React (Vite) · Tailwind CSS · Leaflet (React-Leaflet) · Recharts · Axios.

**What you depend on from teammates:**
- **M6** provides the design system (colors, typography, the AQI indicator spec).
- **M1/M2** provide the backend endpoints. Until an endpoint exists, work against **mock data** shaped like the API so you are never blocked.

> **Golden rule:** never block on the backend. Build a mock API layer first; swap in real calls when endpoints land. The component shouldn't care which it's getting.

---

# Part 1 — Shared Foundation (Weeks 5–6) · *M4 + M5 together*

## Phase 0 — Scaffold that runs (½ day)

1. Create the app: `npm create vite@latest frontend -- --template react-ts`.
2. Install Tailwind and configure it; add the base stylesheet.
3. Install deps: `react-router-dom`, `axios`, `react-leaflet leaflet`, `recharts`.
4. Set up routing in `App.tsx` with placeholder pages (Home, Map, Area, Dashboard, Profile, Report, Admin, Awareness).
5. Add a top-level layout shell (header, nav, content area, footer).

✅ **Done when:** `npm run dev` serves the app, and you can navigate between empty routed pages.

## Phase 1 — Design system & the AQI indicator (1–2 days) · *M6 leads, M4/M5 implement*

1. Translate M6's design tokens into Tailwind config (colors, spacing, fonts).
2. Build shared `common/` components: `Button`, `Card`, `Badge`, `Spinner`, `Modal`, form inputs.
3. ⚠️ Build the **AQI indicator component** — the single most reused piece. It must show **color + text label + icon/pattern** for each of the six EPA categories (Good → Hazardous). Never color alone. Everything (map markers, cards, charts) uses this one component.
4. Build a **reliability badge** component (`official` / `community` / `modelled`) and a **freshness/timestamp** display.
5. Build the loading / empty / error state components you'll reuse everywhere.

✅ **Done when:** a demo page renders all six AQI categories with correct color+label+icon, plus reliability badges — and they pass a contrast check and read correctly in grayscale.

## Phase 2 — API layer, types & auth context (1–2 days) · *M4 + M5*

1. Create `services/api.ts` — an Axios instance with the base URL from `VITE_API_BASE_URL` and an interceptor that attaches the auth token.
2. ⚠️ **Generate types from the backend** instead of hand-writing them: `npx openapi-typescript http://localhost:8000/openapi.json -o src/types/api.ts`. Re-run when the contract changes so frontend and backend never drift.
3. Build a **mock API module** returning realistic sample data (real Kathmandu areas, AQI values spanning categories) so both tracks can build before endpoints exist. A single flag swaps mock ↔ real.
4. Build an **auth context** (`AuthProvider`) holding the current user + token, with `login()`, `logout()`, and a `useAuth()` hook. Keep the access token in memory/context; use the refresh flow to re-issue it (avoids some XSS risk vs. localStorage — note the tradeoff and pick one as a team).
5. Add a `ProtectedRoute` wrapper that redirects guests away from user/admin pages.

✅ **Done when:** any component can call `api.get(...)` (hitting mock or real), read the logged-in user from `useAuth()`, and protected routes redirect when logged out.

---

# Part 2 — Track A: Maps & Visualization (Weeks 6–9) · *M4*

## Phase A1 — Location search & list (1 day)

1. `GET /locations` → render a searchable list of supported areas (typeahead filter).
2. Each list item shows the area name + its AQI indicator (from the shared component).
3. Selecting an area routes to its detail page.

✅ **Done when:** a user can type to filter Kathmandu areas and click through to a detail page.

## Phase A2 — Interactive map (2–3 days) · *the centerpiece of this track*

1. Render a Leaflet map centered on the Kathmandu Valley with React-Leaflet.
2. Place a marker per station from `GET /locations`, colored by AQI category — ⚠️ **plus label/icon**, not color alone (custom marker or tooltip carries the text).
3. Click/hover a marker → popup with AQI, main pollutant, weather, update time, and reliability badge.
4. ⚠️ For areas with **no station**, render the "nearest station: X, 2.3 km" / "no direct data" state — don't invent a solid color.
5. Add the location search box onto the map (fly-to on select).

✅ **Done when:** the valley map shows all stations with accessible colored markers, popups display the honesty fields, and stationless areas show the nearest-station state.

## Phase A3 — Area detail page (1–2 days)

1. Full current reading: AQI (big, via the indicator), category, main pollutant.
2. Pollutant breakdown (PM2.5, PM10, O₃, NO₂, SO₂, CO) + weather.
3. ⚠️ Source, timestamp/freshness, and reliability badge prominently shown.
4. Slot for the trend chart (built next) and the advisory (owned by M5 — agree the shared component boundary).

✅ **Done when:** selecting any area shows a complete, accessible reading with all honesty fields.

## Phase A4 — Trend charts (2 days)

1. `GET /readings/{location_id}?range=24h|7d|30d` → a Recharts line chart.
2. A range toggle (24h / 7d / 30d) that refetches.
3. Handle gaps in data gracefully (missing hours shouldn't break the line).
4. Accessible: chart has an ARIA label/summary; don't rely on color alone to distinguish series.

✅ **Done when:** the chart renders real trend data, the range toggle works, and data gaps are handled.

## Phase A5 — Two-area comparison (1 day)

1. `GET /locations/compare?a=&b=` → show two areas' current readings side by side (and optionally overlaid trend lines).
2. Reuse the AQI indicator and reliability badge for both.

✅ **Done when:** a user can compare two areas (e.g. Kalanki vs Kirtipur) at a glance.

---

# Part 3 — Track B: User & Community (Weeks 6–10) · *M5*

## Phase B1 — Auth screens (1–2 days) · *needs auth context from Phase 2*

1. Register form → `POST /auth/register`, with validation and error display.
2. Login form → `POST /auth/login`, store the token via the auth context.
3. Logout; show the logged-in state in the header.

✅ **Done when:** a user can register, log in, see their logged-in state, and log out — with clear validation errors.

## Phase B2 — Health profile (1–2 days)

1. Profile form: age group, asthma, respiratory, heart condition, pregnancy, outdoor worker, activity level, preferred language — **all optional**.
2. `POST /profile` / `GET /profile` / `PUT /profile`; pre-fill on edit.
3. Make it clear the data is optional and private.

✅ **Done when:** a logged-in user can create, view, and edit their profile, and it persists.

## Phase B3 — Advisory display (1–2 days) · *pairs with M4's area detail*

1. `POST /advisory` for the selected location + profile.
2. Show the risk level using the AQI indicator styling.
3. ⚠️ **Render the reasoning** — the list of reasons the backend returns ("AQI is Unhealthy", "profile includes asthma") — this is the graded differentiator.
4. Always show the "not medical advice" disclaimer.
5. Agree with M4 where this component slots into the area-detail and dashboard layouts.

✅ **Done when:** the advisory shows a personalized recommendation **with its reasons** and a disclaimer, and a child-with-asthma profile visibly shows higher risk than a healthy adult for the same area.

## Phase B4 — Personal dashboard (2 days)

1. Assemble: personal risk summary, saved locations (with AQI indicators), active alerts, a weekly summary, recommended activity time (if in scope).
2. Reuse M4's mini-chart and the AQI indicator.
3. Handle the "no profile yet" and "no favorites yet" empty states.

✅ **Done when:** a logged-in user sees a coherent dashboard pulling their real data, with graceful empty states.

## Phase B5 — Favorites & alerts (1–2 days)

1. Add/remove favorite locations (`/favorites`) from the map, area page, or dashboard.
2. Alert setup UI: pick a saved location + AQI threshold + notification type (`/alerts`).
3. List and toggle existing alerts.

✅ **Done when:** a user can save home/college/work and configure a threshold alert, and it appears in their list.

## Phase B6 — Community reporting (2 days) · *needs file upload*

1. Report form: category, description, location picker (reuse the map), optional photo.
2. `POST /reports` as multipart; show upload progress and validation errors.
3. ⚠️ Client-side validate the image (type, size) before upload; support anonymous submission.
4. "View nearby reports" list + each report's status.

✅ **Done when:** a user can submit a report with a photo, see it accepted as `unverified`, and view nearby reports.

## Phase B7 — Admin dashboard (1–2 days) · *needs admin role*

1. Guard the route to admins only (via `ProtectedRoute` + role check).
2. Moderation queue: list pending reports with verify / reject / flag actions (`PATCH /admin/reports/{id}`).
3. Basic stats cards (`GET /admin/stats`): users, reports by category, flagged items.

✅ **Done when:** a non-admin can't reach the page, and an admin can move a report from `unverified` to `verified`/`rejected` and see it reflected.

---

# Part 4 — Cross-cutting (ongoing) · *both tracks + M6*

Weave these through every phase, don't leave them to the end:

- **Accessibility:** keyboard navigation on all controls; ARIA labels on map, charts, forms; focus states; danger by text+icon not color alone; high-contrast support.
- ⚠️ **i18n (EN / नेपाली):** wire an i18n library (e.g. `react-i18next`) and translation files from the start — retrofitting later is painful. Or explicitly defer in writing.
- **Responsive:** every page works on mobile web (the map and charts especially).
- **Loading / empty / error states:** every data view uses the shared state components.
- **Type sync:** re-run the OpenAPI type generation whenever the backend contract changes.

---

## Build order at a glance

```
SHARED FOUNDATION (M4 + M5 together)
  Phase 0  Scaffold runs
  Phase 1  Design system + AQI indicator   ← reused everywhere
  Phase 2  API layer + types + auth context ← gates both tracks

TRACK A — Maps & Visualization (M4)   |   TRACK B — User & Community (M5)
  A1 Location search & list           |     B1 Auth screens
  A2 Interactive map  ← centerpiece   |     B2 Health profile
  A3 Area detail page                 |     B3 Advisory display ← centerpiece
  A4 Trend charts                     |     B4 Personal dashboard
  A5 Two-area comparison              |     B5 Favorites & alerts
                                      |     B6 Community reporting
                                      |     B7 Admin dashboard

CROSS-CUTTING (both): accessibility · i18n · responsive · states
```

## If you fall behind

The non-negotiable frontend core is: **Phase 1 (AQI indicator) → Phase 2 (API + auth) → A1/A2 (search + map) → A3 (area detail) → B1/B2/B3 (auth + profile + explainable advisory)**. That's the working user journey and the bulk of the marks. Cut in this order: admin polish, comparison view, gamification-style extras, then i18n if truly out of time.

The two "centerpieces" — the **interactive map** (A2) and the **explainable advisory display** (B3) — are what the demo hinges on. Protect them.
