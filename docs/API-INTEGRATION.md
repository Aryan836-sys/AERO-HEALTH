# Backend handoff

## Do not mistake this contract for your team's contract

The supplied guide names endpoints and features but does not provide request/response schemas. `src/types/api.ts` and `contracts/openapi.demo.json` describe the frontend's **assumed demo DTOs**, written to keep frontend work moving. They were not generated from a running FastAPI application.

When your teammate supplies `/openapi.json`, run `npm run types:generate`, then adapt `src/services/api.ts`. Generated types alone do not transform snake_case/camelCase, pagination envelopes, units, IDs, error shapes, or auth response fields.

## Connection sequence

1. Keep `VITE_USE_MOCK_API=true` until the contract and auth session strategy are agreed.
2. Run the backend, retrieve its real OpenAPI schema, and generate `api.generated.ts`.
3. Reconcile the DTOs and response adapters. Prefer explicit normalization at this boundary over scattered fixes in page components.
4. Test cookies, bearer tokens, expired sessions, validation responses, empty profiles, and roles.
5. Set `VITE_API_BASE_URL` and `VITE_USE_MOCK_API=false`, then restart Vite.
6. Verify each page against real data. The UI's mode label reflects configuration, not a certification of data quality.

## Endpoint assumptions currently in the adapter

| Method | Path | Frontend expectation |
| --- | --- | --- |
| GET | `/locations` | `Area[]`, current reading nullable |
| GET | `/readings/{id}?range=24h\|7d\|30d` | `TrendPoint[]`; missing observations use `null` |
| GET | `/locations/compare?a=...&b=...` | `Area[]` for the two selected IDs |
| POST | `/auth/register` | `{name,email,password}` -> `{user,accessToken}` |
| POST | `/auth/login` | JSON email/password -> session (not OAuth form data) |
| POST | `/auth/refresh` | Cookie-authenticated session renewal |
| POST | `/auth/logout` | Server refresh-session invalidation |
| GET | `/profile` | Profile or `null`; 404 is treated as no profile |
| POST / PUT | `/profile` | Create or update profile |
| DELETE | `/profile` | Clear optional profile |
| POST | `/advisory` | `{location_id,profile}` -> reasoned advisory |
| GET / POST | `/favorites` | Read IDs / add `{location_id}` |
| DELETE | `/favorites/{id}` | Remove favorite |
| GET / POST | `/alerts` | Read / create rule |
| PATCH | `/alerts/{id}/toggle` | Toggle rule; server should authorize ownership |
| DELETE | `/alerts/{id}` | Delete rule |
| GET | `/reports` | Array of public report DTOs |
| POST | `/reports` | Multipart fields + optional photo |
| PATCH | `/admin/reports/{id}` | `{status}` moderation update |
| GET | `/admin/stats` | Users, reports, pending, flagged counts |

Refresh/logout/delete-profile and some alert/favorite routes are implementation assumptions beyond the guide's exact method list. Agree these with M1/M2 rather than adding conflicting endpoints unilaterally. Admin category bars currently aggregate the reports returned to the admin page; paginate/aggregate server-side for a larger dataset.

## Fields and units

Area IDs are strings. Positions are decimal WGS84 latitude/longitude. `Reading.aqi` is US AQI, not pollutant concentration. PM2.5, PM10, O3, NO2 and SO2 display micrograms per cubic meter; CO displays milligrams per cubic meter. Confirm and normalize the backend's units before showing real values. Do not relabel ppm/ppb measurements without an appropriate conversion.

Timestamps are ISO strings. Display is Asia/Kathmandu time, while CSV values preserve the UTC timestamp. `source`, `reliability`, `observedAt`, and `isDemo` must come from trusted backend provenance, not be invented client-side. Nearest-station distances are straight-line distances, not walking distances. Pollutant filter colors reflect the overall AQI, not a separately computed pollutant subindex.

The advisory DTO currently uses translation keys plus interpolation values. A backend returning natural-language recommendations needs an adapter or a revised, agreed internationalized contract. Keep advisory severity separate from the underlying station AQI category.

## Auth and privacy

The Axios instance sends credentials and attaches a memory-only access token. A single-flight refresh attempt handles eligible 401 responses. A failed refresh clears the token and emits the session-expired event. The backend must issue and invalidate appropriately secured refresh cookies and enforce authorization on every private endpoint.

Cross-origin credentials require explicit CORS origin handling; a wildcard origin is not compatible with credentialed requests. Review Secure, HttpOnly, SameSite, CSRF protection, consent, retention, and account deletion for the intended deployment. No browser-only check provides real admin authorization or health-data privacy.

## Reports

The browser validates MIME type, nonzero size and a 5 MiB limit, but the server must validate actual content, coordinates, size, permissions and abuse limits again. Production should store photos in controlled object storage and return safe URLs; never trust a client-provided `verified` status or client-reported author identity. Anonymous public display must not accidentally expose personal identifiers.

## Acceptance before real mode

Check authentication refresh and logout; non-admin 403s; ownership of profile/favorites/alerts; profile 404; failed requests/retry; absent and stale readings; out-of-bounds coordinates; large/corrupt files; backend validation details; unit consistency; provenance; report moderation; CORS/cookies; and actual notification delivery, where in scope.
