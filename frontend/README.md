# Aero Health
## A little clarity in every breath.

A complete **frontend demonstration**, built around Kathmandu, Lalitpur, and Bhaktapur. The visual system uses mint-tinted maps, floating station bubbles, white cards, purple controls, readable severity labels, soft motion, and the same navigation and spacing across every page.

This is application source, not a screenshot, a Canva export, or a standalone HTML mockup. It needs Node.js to run. The frontend works without your Python backend in its default demo mode.

## 1. Install these once

- **Node.js LTS**: https://nodejs.org/en/download/ . Node 24 LTS is recommended; the project requires at least 22.12. npm comes with Node.
- **Visual Studio Code**: https://code.visualstudio.com/ . Recommended editor, not required by the application.
- **Git**: optional for running; recommended for your group repository.

Do not separately download React, Tailwind, Leaflet, Recharts, or Axios. `npm install` handles those.

## 2. Run it

Extract the ZIP completely. In VS Code, choose **File > Open Folder** and select the `frontend` folder inside `aero-health-v2`. Open **Terminal > New Terminal**.

```bash
npm install
npm run dev
```

Open the local address printed by Vite, normally **http://localhost:5173/**. Leave the terminal running. Press Ctrl+C to stop it.

The first install needs an internet connection. The street basemap also needs internet; a clear fallback notice appears if tiles cannot load. There are no map API keys to configure for this demo. Google Fonts is optional: system fonts take over if the font service is unavailable. No font files are bundled.

**Windows shortcut:** `start-windows.cmd` is an optional helper inside this folder. It checks for Node/npm, installs dependencies when needed, and starts the dev server. It does not start a backend.

## 3. Try the demo accounts

The sign-in page includes one-click **Explore as a demo user** and **Explore as a demo moderator** buttons.

| Role | Email | Password |
| --- | --- | --- |
| User | demo@aerohealth.local | AeroDemo2026! |
| Moderator | admin@aerohealth.local | AeroAdmin2026! |

You can also register a fictional account. Never enter a real password you use elsewhere or real health information. These are browser-local demos, not secure production accounts.

A useful walkthrough:

1. Explore the homepage map; choose a station, change pollutants, and open an area detail page.
2. Switch 24-hour / 7-day / 30-day trends, reveal the data table, and download CSV data.
3. Compare two areas, then visit Breathe better and compare the adult and child-with-asthma examples.
4. Use the demo-user button, save a location, create an optional profile, and configure an alert on the dashboard.
5. Submit a fictional community report. Then sign out and use the moderator button to verify, reject, or flag it.

## 4. Pages included

| URL | Page |
| --- | --- |
| `/` | Map-first overview, AQI gauge, trend, district cards |
| `/map` | Interactive valley map, filters, search, station list |
| `/areas/ratnapark` | Area reading, six pollutants, weather, trend, advisory |
| `/areas/sankhu` | Explicit no-direct-data example with nearest station |
| `/compare` | Two-area reading and trend comparison |
| `/advisory` | Explainable advisory with saved/adult/child examples |
| `/awareness` | Air-quality essentials, AQI categories, learning cards |
| `/login`, `/register` | Validated demo account flows |
| `/dashboard` | Saved places, weekly context, advisory, alert rules |
| `/profile` | Optional profile creation, editing, and clearing |
| `/community` | Filterable community reports and status details |
| `/community?compose=1` | Anonymous-capable report form and photo validation |
| `/admin` | Role-guarded moderation queue and category statistics |
| `/design-system` | Shared components, six AQI states, contrast mode |

## 5. Project structure

```text
src/
  components/
    common/               Buttons, cards, AQI, modal, states, inputs
    map/                  React-Leaflet map and filters
    charts/               Recharts history/comparison/CSV table
    advisory/             Shared explainable advisory panel
    layout/               Navigation, footer, route guards
  pages/                  Routed page components
  services/
    api.ts                Real Axios adapter + mock/real switch
    mockApi.ts            Asynchronous browser-local demo workflows
    fixtures.ts           Fictional valley readings, reports, trends
    storage.ts            Explicit demo persistence helpers
  context/                Auth, app resources, toast notifications
  hooks/                  Request states and reduced-motion preference
  i18n/                   English and core Nepali translations
  types/                  Provisional frontend DTOs
  utils/                  AQI, geography, validation, export, demo reasoning
```

Styles and design tokens live in `src/index.css` and `tailwind.config.js`. Branding lives in `components/common/Logo.tsx` and `public/favicon.svg`. Most fixture changes belong in `services/fixtures.ts`, not in a page component.

## 6. What is genuinely implemented, and what is simulated?

The navigation, controls, map interactions, forms, validation, profile editing, favorites, alert rule changes, report submission, upload preview/progress, moderation, data tables, and CSV export are implemented frontend behaviors.

The default dataset, historical series, optional projection, weather, advisories, accounts, incidents, and source labels are **fictional**. Even a badge reading `Demo - Official` is an example of a source type, not a claim that a real official station measured that value. The source assignments and approximate station coordinates are fixtures, not a verified station inventory.

Alert rules do not send email, push notifications, or run monitoring jobs. The bell only checks the current demo snapshot in the open application. The projection toggle is explicitly a sample, not a forecast model. Personal risk is a separate illustrative output; it never changes the area's underlying AQI category. No medical decisions should be based on this demo.

The street map uses real map tiles, while markers display fictional point readings. There is intentionally no invented heatmap or blanket pollution coloring for unmeasured neighborhoods.

**Language scope:** the i18n library is wired throughout. English is complete for the translation catalog. Core Nepali navigation, AQI labels, location names, and common actions are translated; extended copy falls back to English. Finishing and native-reviewing the remaining Nepali copy is explicitly deferred. Some editorial eyebrows and backend/mock error strings remain English.

## 7. Data persistence and privacy

| Data | Demo storage | Lifetime |
| --- | --- | --- |
| Access token | Memory/context | Current page runtime |
| Demo user ID | Session storage | This browser tab |
| Registered demo accounts / password demo hashes | Session storage | This browser tab |
| Optional health profile | Session storage, per user | This browser tab |
| Favorites and alert rules | Local storage, per user | Until site data is cleared |
| Community reports / downsized photos | Local storage | Until site data is cleared |
| Preferred interface language | Local storage | Until site data is cleared |

A frontend role guard is a UI boundary, **not a security boundary**. Browser storage can be edited by the person using the browser. The demo password digest is not suitable for real account security. Production auth, authorization, validation, medical rules, rate limiting, file processing, retention, and privacy protections belong on the backend.

To reset the demo, use your browser's site-data controls for `localhost:5173`, then reload. This deletes demo reports and saved choices. Closing the tab clears temporary data in a normal browser session, but some browsers can restore session storage when restoring tabs; do not use this demo for sensitive information.

## 8. Checks and production build

```bash
npm run lint          # Source paths, syntax, and English translation-key audit
npm test              # 54 tests of the actual project utilities/mock services
npm run typecheck     # Full dependency-aware TypeScript check
npm run build         # TypeScript + Vite production build
npm run preview       # Serve the resulting dist/ locally
```

Optional full browser tests:

```bash
npx playwright install chromium
npm run test:e2e
```

The Playwright configuration builds and previews the real application, then runs desktop and mobile tests. These tests do not require map tile service availability.

Formatting:

```bash
npm run format
npm run format:check
```

The source is formatted into separate readable components. The Prettier commands give your whole team one formatter after dependencies are installed.

**Authoring validation:** 54 project-logic tests passed; the source audit passed; constrained desktop/mobile source renders and selected demo interactions were checked. Outbound npm downloads were unavailable in the authoring environment, so the dependency-installed production build and full Playwright suite are supplied **but not yet verified**. Do not treat the local source-render checks as certification of the actual Leaflet, Recharts, React 19, Vite, or router package integrations.

A `package-lock.json` could not be produced without resolving the dependencies. Your first successful `npm install` creates it. Commit that lockfile, then use `npm ci` for reproducible team/CI installs.

## 9. Backend connection later

Copy `.env.example` to `.env.local` and leave demo mode enabled until the backend contract is ready.

```dotenv
VITE_USE_MOCK_API=true
VITE_API_BASE_URL=http://localhost:8000
```

When the backend is running:

```bash
npm run types:generate
# Or specify its actual OpenAPI URL:
npm run types:generate -- http://localhost:8000/openapi.json
```

This writes `src/types/api.generated.ts`. Reconcile `services/api.ts` against the generated schema and test the refresh-cookie flow before setting `VITE_USE_MOCK_API=false`. The supplied guide had endpoint names but no schema, so the current DTOs are explicitly provisional. Toggling the flag alone cannot resolve unknown backend differences. See `../docs/API-INTEGRATION.md`.

A separate `npm run types:generate -- --demo` command generates from the included fictional demo contract; it is not evidence of backend compatibility.

## 10. Deploying the frontend

Only after the build and browser tests pass, deploy `dist/` to a static host. For a Git-based Vercel or Netlify project, set the project root to `frontend`, the build command to `npm run build`, and the publish directory to `dist`. SPA rewrite examples are included in `vercel.json` and `public/_redirects`.

Use HTTPS for deployments. Geolocation and the demo registration hashing require a secure context; `localhost` is normally treated as secure for development. Configure the real backend's CORS, secure refresh cookie, origins, rate limits, and server authorization separately. `VITE_*` variables are visible to visitors; never put a private API key in them. Review your map provider's terms before a public production launch.

No site has been deployed and no external account has been modified by this delivery.

## Troubleshooting

**Do not double-click `index.html`.** React source needs the Vite dev server or a built deployment.

**`node` or `npm` is not recognized:** finish installing Node LTS, close VS Code, reopen it, then run `node -v` and `npm -v`.

**PowerShell blocks `npm.ps1`:** use VS Code's Command Prompt terminal, or run `npm.cmd install` and `npm.cmd run dev`. You do not need to loosen the computer's execution policy.

**Port 5173 is already in use:** stop the other Vite terminal or run `npm run dev -- --port 5174` and use the printed address.

**No streets appear:** internet access to the tile provider may be blocked. Use the retry control; area lists, coordinates, and demo readings still work. The app never fabricates replacement map geography.

**Registered account disappears:** tab-local demo accounts are intentional. Use the built-in accounts again or create another fictional registration.

**Profile is blank after closing the tab:** temporary storage is intentional. Favorites/reports are stored separately.

**An install/build fails:** preserve the first error message. Check the Node version, connection, and proxy settings before changing package versions or deleting files. Do not use `npm audit fix --force` without reviewing the resulting dependency changes.
