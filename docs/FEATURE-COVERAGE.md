# Coverage against the supplied build guide

The original guide and folder structure are retained in `docs/reference/`. The implementation is **frontend-only and mock-backed by default**. A completed frontend interaction is not a claim that its backend endpoint exists.

| Guide phase | Delivered frontend | Integration / validation boundary |
| --- | --- | --- |
| Phase 0 | React/TS/Vite structure, routes, common shell | Full npm-resolved build must be run locally |
| Phase 1 | AQI indicator/gauge, six categories, badges, source/time, states, buttons/cards/modal, design showcase | Only badge color-pair contrast assertions automated; full accessibility audit pending |
| Phase 2 | Typed service interface, async mocks, Axios adapter, memory access token, refresh flow, protected routes | DTOs are provisional; no teammate OpenAPI was supplied |
| A1 | Searchable area list, click to area detail, shared indicators | All readings are fixtures |
| A2 | React-Leaflet valley map, point markers, filters, map controls, selected-area fly-to, source/weather/time popup | External map tiles require internet; actual package rendering not verified here |
| A3 | AQI, six pollutants, weather, source, timestamp, trend, advisory | Station inventory/source assignments not verified real stations |
| A4 | 24h/7d/30d history, gaps, comparison series, summary/table/CSV, explicitly sample projection | No measured history or real forecast provider |
| A5 | Two-area selectors, swap, reading comparison, overlaid trends, pollutant table | Mock compare service |
| B1 | Validated login/register, logout, demo-role entry points | Browser-local simulation; server auth/security required |
| B2 | Optional age/conditions/activity/language, prefill/edit/clear, privacy notice | Tab-local demo profile, not a private health-data service |
| B3 | Risk, recommendation, reason list, adult/child examples, disclaimer | Demo reasoning only; backend must own validated rules |
| B4 | Saved-location dashboard, weekly chart, profile/advisory, active alert summary, empty states | Activity-time prediction is explicitly not included |
| B5 | Save/remove favorites; create, toggle, delete threshold rules; in-app snapshot bell | No email/push/background notification delivery |
| B6 | Category/description/area/map coordinates, anonymous submission, optional photo, type/size validation, preview/progress, nearby-area filters, status/detail | Local demo storage, no upload server, no verification of incidents |
| B7 | Admin route guard, pending queue, verify/reject/flag, statistics and category distribution | Server enforcement and moderation audit log still required |
| Cross-cutting | Shared CSS, mobile layouts, focus/reduced motion, table alternatives, error/empty/loading states, wired i18n | Core Nepali only; extended translations and native review explicitly deferred |

## Changes from the v1 archive

The earlier archive was reviewed as a prototype, not treated as a finished implementation. This delivery adds the multi-page architecture, working demo services and persistence, auth/profile/community/admin flows, shared design components, meaningful controls, explicit data-source limitations, tests, and integration documentation. It does not modify or bundle a backend.
