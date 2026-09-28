# Aero Health — Backend

FastAPI + PostgreSQL/PostGIS backend for real-time air-quality data,
health advisories, favorites, alerts, and community pollution reports
for the Kathmandu Valley.

---

## 1. Environment setup

**Requirements:** Python 3.11+, PostgreSQL 14+ with the PostGIS
extension, `pip`.

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Copy the example environment file and fill in real values (see
[Section 3](#3-environment-variables) for what each one does):

```bash
cp .env.example .env
```

---

## 2. Database setup

1. Create a database with the PostGIS extension enabled:

   ```sql
   CREATE DATABASE aero_health;
   \c aero_health
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```

2. Point `DATABASE_URL` in `.env` at it, then run every migration:

   ```bash
   python -m alembic upgrade head
   ```

3. Seed the Kathmandu Valley monitoring stations from WAQI's live
   station list:

   ```bash
   python -m app.scripts.seed_locations
   ```

4. (Optional) Populate real AQI readings — needs `WAQI_TOKEN` and, for
   the fallback chain, `OPENAQ_API_KEY` and `OPENWEATHER_API_KEY` set
   first:

   ```bash
   python -m app.jobs.cache_readings
   # or, to keep it running and re-fetch every AQI_CACHE_INTERVAL_MINUTES:
   python -m app.jobs.cache_readings --loop
   ```

5. (Optional) Create your first admin account — there is intentionally
   no API endpoint for this (see [Known limitations](#5-known-limitations)):

   ```bash
   python -m app.scripts.promote_admin your-email@example.com
   ```

Run the server:

```bash
python -m uvicorn app.main:app --reload
```

Confirm both the API and the database are reachable:

```
GET http://localhost:8000/health
→ {"api": "ok", "database": "ok", "error": null}
```

Interactive API docs (Swagger UI) are at `http://localhost:8000/docs`.

---

## 3. Environment variables

| Variable | Required? | Purpose |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string, e.g. `postgresql+psycopg2://user:pass@localhost:5432/aero_health` |
| `WAQI_TOKEN` | Yes, for real AQI data | Free token from [aqicn.org/data-platform/token](https://aqicn.org/data-platform/token/) |
| `OPENAQ_API_KEY` | Yes, for the fallback chain | Free key from [explore.openaq.org/register](https://explore.openaq.org/register) |
| `OPENWEATHER_API_KEY` | Yes, for weather + fallback | Free key from [home.openweathermap.org](https://home.openweathermap.org/users/sign_up) — new keys can take up to a few hours to activate |
| `JWT_SECRET_KEY` | Yes | No default on purpose — a shared default would let anyone forge a valid token. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_ALGORITHM` | No (default `HS256`) | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No (default `30`) | Access token lifetime |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | No (default `14`) | Refresh token lifetime |
| `CORS_ORIGINS` | No (default `http://localhost:5173`) | Comma-separated list of allowed frontend origins |
| `AQI_CACHE_INTERVAL_MINUTES` | No (default `30`) | How often `cache_readings.py --loop` re-fetches |

---

## 4. API endpoints

All endpoints are unprefixed (no `/api/v1`) — call them directly, e.g.
`http://localhost:8000/locations`.

### Health
| Method | Path | Auth |
|---|---|---|
| GET | `/` | none |
| GET | `/health` | none |

### Locations & readings
| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/locations` | none | All monitored locations + each one's latest cached reading |
| GET | `/locations/{id}` | none | One location; `reading: null` if nothing cached yet |
| GET | `/readings/{location_id}?range=24h\|7d\|30d` | none | Trend data, oldest first |

### Auth
| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/auth/register` | none | |
| POST | `/auth/login` | none | Returns `access_token` + `refresh_token` |
| POST | `/auth/refresh` | none | Takes `{"refresh_token": "..."}` in the body |
| GET | `/auth/me` | required | Proves a token actually protects an endpoint |

### Health profile
| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/profile` | required | Create/upsert your own profile |
| GET | `/profile` | required | 404 if you haven't set one yet |
| PUT | `/profile` | required | |

### Advisory
| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | `/advisory/{location_id}` | optional | Works for guests; personalizes if you're logged in and have a profile. 404 if no reading cached yet; 503 if the cached reading has no usable `aqi` |

### Favorites
| Method | Path | Auth |
|---|---|---|
| POST | `/favorites` | required |
| GET | `/favorites` | required |
| DELETE | `/favorites/{location_id}` | required |

### Alerts
| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/alerts` | required | `aqi_threshold` must be 0–500 |
| GET | `/alerts` | required | |
| PATCH | `/alerts/{alert_id}` | required | Activate/deactivate; 404 if it isn't yours |

### Pollution reports
| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/reports` | optional | Anonymous submissions are allowed by design |
| GET | `/reports?verification_status=` | none | Optional status filter |

### Admin (all require the `admin` role)
| Method | Path | Notes |
|---|---|---|
| GET | `/admin/reports?verification_status=unverified` | The moderation queue |
| PATCH | `/admin/reports/{id}` | Set `verification_status` to `verified`/`rejected`/`flagged`/`unverified`; writes an audit log entry |
| GET | `/admin/stats` | Basic counts |
| GET | `/admin/audit-log` | Every admin action ever taken |

---

## 5. Known limitations

- **Frontend auth contract mismatch.** The frontend's existing
  `AuthContext.tsx` expects a different shape than this backend
  returns — a nested `user` object in the login/register response, an
  httpOnly-cookie-based refresh flow, `name` instead of `full_name`,
  and `role: 'user'|'admin'` instead of `'guest'|'registered'|'admin'`.
  Locations/readings are connected and working; auth, profile,
  favorites, alerts, and reports are **not yet** wired to the frontend
  UI — an adapter layer (similar to `schemas/frontend_area.py`) is
  needed before those forms will work as-is.
- **EPA AQI is only computed for PM2.5 and PM10.** OpenAQ-sourced
  readings get a real AQI from those two pollutants; O3/NO2/SO2/CO
  breakpoints are in ppb/ppm (not µg/m³), and converting them
  incorrectly would be worse than not computing an AQI at all — so
  they're deliberately left as raw concentrations only.
- **No image upload endpoint.** Pollution reports accept an
  `image_url` string; there's no multipart file-upload handling. The
  work plan marked this "if time permits."
- **WAQI availability is region-dependent and outside this project's
  control.** During development, WAQI's `/feed/` endpoint had extended
  outages for Nepal-region stations specifically (confirmed via direct
  HTTP checks — 200 responses with a graceful `"can not connect"`
  body, not a timeout or auth failure). The reliability fallback chain
  (WAQI → OpenAQ → last cached reading) exists specifically to handle
  this in production.
- **No admin self-service.** There is no API endpoint to become an
  admin — deliberately, since one would be a privilege-escalation
  risk. The first admin must be created via
  `python -m app.scripts.promote_admin <email>`, which requires direct
  server/database access.
- **`requirements.txt` must be UTF-8.** If you see it fail to parse or
  `pip install` silently do nothing, it may have been saved as UTF-16
  by a Windows tool (e.g. PowerShell's `pip freeze >`). Re-save it as
  UTF-8.

---

## 6. Testing

```bash
# Everything except the job tests, which need a live database:
python -m pytest app/tests --ignore=app/tests/jobs -v

# The caching job's own tests (needs DATABASE_URL pointed at a real,
# migrated database with at least one seeded location):
python -m pytest app/tests/jobs -v
```

Test layout:
- `app/tests/adapters/` — WAQI/OpenAQ/OpenWeatherMap parsing, the
  normalizer, the EPA AQI calculator, and the reliability/fallback chain
- `app/tests/core/` — password hashing, JWT, and the auth dependencies
- `app/tests/crud/` — direct database-query logic (e.g. the
  `get_latest_reading` null-AQI filter)
- `app/tests/routers/` — every HTTP endpoint, mocked at the database
  boundary
- `app/tests/services/` — the advisory engine's AQI-category and
  recommendation logic
- `app/tests/integration/` — full request chains spanning multiple
  routers (location → AQI → advisory; login → profile → advisory)
- `app/tests/jobs/` — the scheduled caching job (needs a real database)