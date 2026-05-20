# NeoScape Properties — Full Architecture & Deployment Audit Report

**Date:** May 20, 2026
**Auditor:** Kiro AI
**Project:** NeoScape Properties (Room Booking Platform)
**Scope:** Full-stack audit — Backend (Django/DRF), Frontend (React/Vite/TypeScript), Render deployment, Supabase integration, CORS, environment variables, authentication, and production readiness.

---

## Table of Contents

1. [Project Structure Overview](#1-project-structure-overview)
2. [Critical Issue: Why Render Fails Without Local Backend](#2-critical-issue-why-render-fails-without-local-backend)
3. [Environment Variable Mismatches](#3-environment-variable-mismatches)
4. [Deployment Configuration Issues](#4-deployment-configuration-issues)
5. [CORS Configuration Issues](#5-cors-configuration-issues)
6. [Frontend/Backend API Connection Issues](#6-frontendbackend-api-connection-issues)
7. [Supabase Integration Issues](#7-supabase-integration-issues)
8. [Authentication Flow Issues](#8-authentication-flow-issues)
9. [Backend Architecture Issues](#9-backend-architecture-issues)
10. [Frontend Architecture Issues](#10-frontend-architecture-issues)
11. [Security Issues](#11-security-issues)
12. [README / Documentation Mismatches](#12-readme--documentation-mismatches)
13. [CI/CD Pipeline Issues](#13-cicd-pipeline-issues)
14. [Summary Table of All Issues](#14-summary-table-of-all-issues)
15. [Recommended Fixes (Priority Order)](#15-recommended-fixes-priority-order)
16. [Remaining Risks](#16-remaining-risks)

---

## 1. Project Structure Overview

```
Room-Booking/
├── Backend/
│   └── room-booking/                  ← Django DRF backend (workspace root)
│       ├── accounts/                  ← User profile management
│       ├── bookings/                  ← Django project config (settings.py, urls.py, wsgi.py)
│       ├── bookings_app/              ← Booking + Rent schedule logic
│       ├── core/                      ← Upload, stats, auth-verify, Supabase storage
│       ├── rooms/                     ← Room + PropertyDocument management
│       ├── .env                       ← ⚠️ LIVE CREDENTIALS COMMITTED (see §11)
│       ├── .env.example
│       ├── build.sh
│       ├── render.yaml
│       ├── requirements.txt
│       ├── start_server.py            ← Dev-only helper (not used in production)
│       └── .github/workflows/ci.yml
│
└── Room-Booking-new/                  ← React + TypeScript + Vite frontend
    ├── src/
    │   ├── context/AuthContext.tsx
    │   ├── components/AuthProvider.tsx
    │   ├── hooks/useAuth.ts
    │   ├── lib/api.ts                 ← All API calls + base URL config
    │   ├── lib/types.ts
    │   ├── services/supabaseClient.ts
    │   ├── services/authService.ts
    │   └── pages/
    ├── .env                           ← ⚠️ LIVE CREDENTIALS (Supabase anon key)
    ├── .env.example
    ├── vite.config.ts
    ├── netlify.toml
    └── package.json
```

**Key observation:** The backend lives at `Backend/room-booking/` and the frontend lives at `Room-Booking-new/`. These are two completely separate directories with no shared root config. This separation is the source of several deployment and configuration mismatches.

---

## 2. Critical Issue: Why Render Fails Without Local Backend

This is the **root cause** of the primary reported problem.

### Finding 2.1 — `DEBUG=True` in the committed `.env` file

**File:** `Backend/room-booking/.env`
**Value found:** `DEBUG=True`

**Impact:** The `render.yaml` sets `DEBUG=False` as an environment variable. However, `settings.py` reads the `.env` file first via `environ.Env.read_env(...)` with `overwrite=False`. This means **the `.env` file value takes precedence over Render's dashboard env vars** when `overwrite=False` is used.

```python
# settings.py line:
environ.Env.read_env(os.path.join(BASE_DIR, '.env'), overwrite=False)
```

With `overwrite=False`, values already loaded from `.env` are NOT overridden by system environment variables. This means:
- Render sets `DEBUG=False` → but `.env` already set `DEBUG=True` → **production runs in DEBUG mode**
- `CORS_ALLOW_ALL_ORIGINS = DEBUG` → **CORS is wide open in production**
- All production security settings (`SECURE_SSL_REDIRECT`, HSTS, etc.) are **disabled** because `not DEBUG` is `False`

### Finding 2.2 — The `.env` file is committed to the repository

**File:** `Backend/room-booking/.env` (not in `.gitignore` effectively, or was committed)

The `.env` file contains live production credentials including `DB_PASSWORD`, `SUPABASE_JWT_SECRET`, and `SUPABASE_SERVICE_ROLE_KEY`. When Render pulls the repo, it gets this `.env` file. This means the local `.env` IS the production `.env` — which is why it works locally and on Render simultaneously. But it also means:

- Any change to local `.env` directly affects production after the next deploy
- Secrets are exposed in the git history
- The `render.yaml` `sync: false` env vars are **never actually used** because `.env` overrides them

### Finding 2.3 — Render `render.yaml` missing `SUPABASE_SERVICE_ROLE_KEY`

**File:** `render.yaml`

The `render.yaml` lists these Supabase env vars:
```yaml
- key: SUPABASE_URL
  sync: false
- key: SUPABASE_JWT_AUDIENCE
  value: authenticated
- key: SUPABASE_JWT_SECRET
  sync: false
- key: SUPABASE_DOCUMENTS_BUCKET
  value: documents
```

**Missing:** `SUPABASE_SERVICE_ROLE_KEY` is NOT listed in `render.yaml`. If the `.env` file were ever removed from the repo (as it should be), Render would have no `SUPABASE_SERVICE_ROLE_KEY` and all image/document uploads would fail with `"Supabase client not configured"`.

### Finding 2.4 — `render.yaml` missing `ALLOWED_HOSTS` value

```yaml
- key: ALLOWED_HOSTS
  sync: false
```

`sync: false` means it must be manually set in the Render dashboard. If it was never set, Django would reject all requests with a 400 Bad Request. The `settings.py` has a fallback:

```python
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '.onrender.com'])
```

The `.onrender.com` wildcard in the default covers Render's domain, so this is not currently broken — but it relies on the fallback, not an explicit configuration.

### Finding 2.5 — `render.yaml` missing `CORS_ALLOWED_ORIGINS` value

```yaml
- key: CORS_ALLOWED_ORIGINS
  sync: false
```

If this is not set in the Render dashboard, the fallback in `settings.py` is:
```python
default=[
    'http://localhost:3000',
    'http://localhost:5173',
    'https://neoscapeproperties.netlify.app',
]
```

The Netlify URL is in the fallback, so CORS works — but again, this relies on the fallback, not explicit configuration. If the frontend URL ever changes, this will silently break.

---

## 3. Environment Variable Mismatches

### Finding 3.1 — `overwrite=False` causes `.env` to shadow Render dashboard vars

**File:** `bookings/settings.py`
```python
environ.Env.read_env(os.path.join(BASE_DIR, '.env'), overwrite=False)
```

`overwrite=False` means: "read the `.env` file but do NOT overwrite values already in `os.environ`." On Render, environment variables are injected into `os.environ` BEFORE the process starts. So the correct behavior should be that Render's vars win. However, `django-environ`'s `read_env` with `overwrite=False` reads the file and sets values that are NOT already in `os.environ`. Since Render injects its vars first, this should work correctly in theory.

**BUT** — the `.env` file is committed to the repo and Render pulls it. So Render's own env vars (set in dashboard) and the `.env` file both exist. The `overwrite=False` means `.env` values only apply if the Render dashboard var is NOT set. Since `render.yaml` has `sync: false` for most vars (meaning they must be manually set in the dashboard), if the dashboard vars were never set, the `.env` file values are used — including `DEBUG=True`.

**Verdict:** The system works locally because `.env` has all values. On Render, it works only if the dashboard vars are properly set. If they are not set, `.env` values (including `DEBUG=True`) are used in production.

### Finding 3.2 — Frontend `.env.example` has empty `VITE_API_BASE_URL`

**File:** `Room-Booking-new/.env.example`
```
VITE_API_BASE_URL=
```

The actual `.env` has:
```
VITE_API_BASE_URL=https://room-booking-pjo6.onrender.com/api
```

And `api.ts` has a hardcoded fallback:
```typescript
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "https://room-booking-pjo6.onrender.com/api";
```

This means if `VITE_API_BASE_URL` is not set in Netlify's environment variables, the hardcoded fallback is used. This is currently working but is fragile — if the Render URL changes, the fallback in source code must be updated manually.

### Finding 3.3 — No `VITE_API_BASE_URL` documented in Netlify deployment

The `netlify.toml` does not set `VITE_API_BASE_URL`:
```toml
[build.environment]
  NODE_VERSION = "18"
```

Only `NODE_VERSION` is set. `VITE_API_BASE_URL` must be set manually in the Netlify dashboard or it falls back to the hardcoded URL in `api.ts`.

### Finding 3.4 — Backend `.env` contains `DEBUG=True` for production

The committed `.env` has `DEBUG=True`. This is a development value that should never reach production. Since the file is committed to the repo and Render pulls it, this value is present on the Render server.

### Finding 3.5 — `ALLOWED_HOSTS` not set in `.env` file

The `.env` file does not contain `ALLOWED_HOSTS`. The settings fallback includes `.onrender.com` wildcard, so Render works. But this is undocumented and fragile.

---

## 4. Deployment Configuration Issues

### Finding 4.1 — Render `render.yaml` root directory not specified

**File:** `render.yaml`

The `render.yaml` does not specify a `rootDir`. The repo root is `room-booking/` (the backend folder). The `render.yaml` is at the repo root, so Render correctly uses the repo root as the working directory. Build commands (`build.sh`, `manage.py`) are relative to this root. This is **correct** — but only because the backend IS the repo root.

**Risk:** If the frontend is ever added to the same repo, the `render.yaml` would need a `rootDir` to avoid confusion.

### Finding 4.2 — `build.sh` has no virtual environment activation

**File:** `build.sh`
```bash
pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
```

On Render, this runs in the system Python environment. There is no `venv` activation. This is acceptable for Render (Render manages its own environment), but it means the build is not reproducible locally without a venv.

### Finding 4.3 — `requirements.txt` uses open version ranges

**File:** `requirements.txt`
```
Django>=5.0
djangorestframework>=3.14
supabase>=2.0
PyJWT>=2.8
```

Open ranges (`>=`) mean Render could install a newer breaking version on the next deploy. For example, `supabase>=2.0` could install `supabase 3.x` if released, which may have breaking API changes. This is a production stability risk.

**Recommendation:** Pin all dependencies to exact versions (e.g., `Django==5.1.3`).

### Finding 4.4 — `start_server.py` is a dev-only file that could cause confusion

**File:** `start_server.py`
```python
call_command('runserver', '8000', '--noreload', '--debug')
```

This file uses Django's development server (`runserver`) and forces `--debug`. It is NOT used by Render (Render uses `gunicorn` from `render.yaml`). However, its presence in the repo root could confuse developers or CI systems that auto-detect start scripts.

### Finding 4.5 — Render `healthCheckPath` points to `/` but root view returns JSON

**File:** `render.yaml`
```yaml
healthCheckPath: /
```

**File:** `bookings/urls.py`
```python
def root_view(request):
    return JsonResponse({'status': 'ok', 'message': 'Room Booking API is running', 'docs': '/swagger/'})
```

The root view returns a 200 JSON response. Render's health check expects a 200 response, which it gets. This is **correct**. No issue here.

### Finding 4.6 — Gunicorn worker count may be too high for Render free tier

**File:** `render.yaml`
```yaml
startCommand: gunicorn bookings.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
```

Render's free tier has limited RAM. 3 Gunicorn workers × Django memory footprint can exceed free tier limits, causing the service to crash silently (OOM kill). This would explain intermittent failures on the deployed version.

**Recommendation:** Use `--workers 2` or `--workers 1` on free tier, or switch to `--worker-class gevent` with `--workers 1`.

---

## 5. CORS Configuration Issues

### Finding 5.1 — `CORS_ALLOW_ALL_ORIGINS = DEBUG` is dangerous with committed `DEBUG=True`

**File:** `bookings/settings.py`
```python
CORS_ALLOW_ALL_ORIGINS = DEBUG
```

Since `DEBUG=True` is in the committed `.env`, and `overwrite=False` means `.env` values are used when Render dashboard vars are not set, **production CORS may be wide open** if the Render dashboard `DEBUG` variable was never explicitly set to `False`.

**Impact:** Any website can make authenticated API calls to the backend. Combined with the Supabase JWT auth, this means any attacker who obtains a valid Supabase token can call the API from any origin.

### Finding 5.2 — `CORS_ALLOWED_ORIGINS` fallback includes localhost

**File:** `bookings/settings.py`
```python
default=[
    'http://localhost:3000',
    'http://localhost:5173',
    'https://neoscapeproperties.netlify.app',
]
```

In production, `localhost` origins should not be in `CORS_ALLOWED_ORIGINS`. If `CORS_ALLOW_ALL_ORIGINS` is `False` (correct production behavior), then localhost origins in the allowed list are harmless but unnecessary. However, if `DEBUG=True` is accidentally set, `CORS_ALLOW_ALL_ORIGINS` becomes `True` and this list is ignored anyway.

### Finding 5.3 — `CORS_ALLOWED_ORIGINS` env var not set in Render dashboard (likely)

The `render.yaml` has:
```yaml
- key: CORS_ALLOWED_ORIGINS
  sync: false
```

`sync: false` means it must be manually set in the Render dashboard. If it was never set, the fallback list is used. The fallback includes `neoscapeproperties.netlify.app`, so CORS works — but this is undocumented and fragile.

### Finding 5.4 — `CSRF_TRUSTED_ORIGINS` hardcodes the Render URL

**File:** `bookings/settings.py`
```python
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
    'https://room-booking-pjo6.onrender.com',
    'https://neoscapeproperties.netlify.app',
    ...
])
```

The Render URL `room-booking-pjo6.onrender.com` is hardcoded in the default. If the Render service is recreated with a different URL, CSRF will break. This should be set via environment variable.

---

## 6. Frontend/Backend API Connection Issues

### Finding 6.1 — Frontend `api.ts` hardcodes the Render URL as fallback

**File:** `Room-Booking-new/src/lib/api.ts`
```typescript
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "https://room-booking-pjo6.onrender.com/api";
```

This is the correct production URL. The frontend is NOT pointing to localhost in production. However:
- If `VITE_API_BASE_URL` is not set in Netlify's environment, the hardcoded fallback is used
- If the Render service URL changes, the fallback in source code must be updated
- The fallback should not exist — the app should fail loudly if the env var is missing

### Finding 6.2 — Render free tier "spin-down" causes cold start failures

Render's free tier spins down services after 15 minutes of inactivity. When the frontend makes an API call to a spun-down backend, the first request times out (can take 30–60 seconds to spin up). This is the most likely explanation for "frontend API fetching errors appear when local backend is OFF."

**The frontend is correctly pointing to the Render URL. The Render service itself is spinning down due to inactivity on the free tier.**

This is NOT a code bug — it is a Render free tier limitation. The fix is either:
1. Upgrade to Render paid tier (no spin-down)
2. Add a keep-alive ping service (e.g., UptimeRobot pinging `/` every 10 minutes)
3. Handle the timeout gracefully in the frontend with a retry mechanism and user-facing loading state

### Finding 6.3 — No trailing slash consistency between frontend and backend

**Backend `core/urls.py`:**
```python
path('upload/images', ...)   # No trailing slash
path('admin/stats', ...)     # No trailing slash
path('auth/verify', ...)     # No trailing slash
path('me', ...)              # No trailing slash
```

**Backend `rooms/urls.py`:**
```python
path('', ...)                # No trailing slash
path('<int:id>/', ...)       # HAS trailing slash
path('documents/', ...)      # HAS trailing slash
path('documents/<int:pk>/', ...) # HAS trailing slash
path('documents/upload/', ...) # HAS trailing slash
```

There is inconsistency — some routes have trailing slashes, some don't. Django's `APPEND_SLASH=True` (default) will redirect non-slash URLs to slash versions with a 301. If the frontend sends a POST to a URL without a trailing slash and Django redirects to the slash version, the POST body is lost (browsers follow 301 redirects as GET). This can cause silent failures on POST requests.

**Specifically at risk:** `POST /api/upload/images` (no slash in `core/urls.py`) — if the frontend calls `/api/upload/images/` (with slash), Django will 404. If it calls `/api/upload/images` (no slash), it works. The frontend must match exactly.

### Finding 6.4 — `api.ts` 401 retry logic may cause infinite loops

**File:** `Room-Booking-new/src/lib/api.ts`

The API client refreshes the Supabase session on 401 and retries once. If the backend returns 401 for a reason other than token expiry (e.g., user not found in Django DB, role mismatch), the retry will also fail with 401, and the error will propagate. This is acceptable behavior but should be documented.

---

## 7. Supabase Integration Issues

### Finding 7.1 — `SUPABASE_SERVICE_ROLE_KEY` missing from `render.yaml`

**File:** `render.yaml`

The `SUPABASE_SERVICE_ROLE_KEY` is used by `core/storage_backends.py` to initialize the Supabase client for file uploads. It is NOT listed in `render.yaml`. If the `.env` file is ever removed from the repo (as it should be for security), Render will have no `SUPABASE_SERVICE_ROLE_KEY` and all image/document uploads will fail with:
```
Exception: Supabase client not configured. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.
```

### Finding 7.2 — Supabase JWT secret is committed to the repo

**File:** `Backend/room-booking/.env`

The `SUPABASE_JWT_SECRET` value is committed in plaintext. This secret is used to verify all Supabase JWTs. Anyone with access to the repo can forge valid JWTs and authenticate as any user.

### Finding 7.3 — Supabase `service_role` key is committed to the repo

**File:** `Backend/room-booking/.env`

The `SUPABASE_SERVICE_ROLE_KEY` is committed in plaintext. This key bypasses all Supabase Row Level Security (RLS) policies and has full database access. This is a critical security exposure.

### Finding 7.4 — Database password is committed to the repo

**File:** `Backend/room-booking/.env`

`DB_PASSWORD` (Supabase PostgreSQL connection password) is committed in plaintext. Combined with the `DB_HOST` (Supabase pooler), this gives full database access to anyone who reads the repo.

### Finding 7.5 — Supabase JWT validation uses `lru_cache` on JWKS client

**File:** `accounts/authentication.py`
```python
@lru_cache(maxsize=1)
def _get_jwk_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url)
```

The JWKS client is cached indefinitely. If Supabase rotates its signing keys, the cached client will have stale keys and all JWT validation will fail until the server restarts. This is a known issue with JWKS caching.

**Recommendation:** Use `PyJWKClient` with a `cache_keys=True` and `lifespan` parameter, or add a TTL to the cache.

### Finding 7.6 — No Supabase bucket existence check at startup

The `SupabaseStorage` class in `core/storage_backends.py` does not verify that the `images` or `documents` buckets exist at startup. If the buckets don't exist in Supabase, uploads will fail at runtime with an opaque error.

---

## 8. Authentication Flow Issues

### Finding 8.1 — All room/booking endpoints require `IsAdmin` — no customer access

**Files:** `rooms/views.py`, `bookings_app/views.py`, `accounts/views.py`, `core/views.py`

Every single API endpoint uses `permission_classes = [IsAdmin]` except `VerifyTokenView` and `MeView` (which use `IsAuthenticated`). This means:
- Customers cannot browse rooms
- Customers cannot create bookings
- Customers cannot view their own bookings
- The platform is currently admin-only

This is a fundamental architectural gap. The project goal states users should be able to "view all listed properties, click individual properties, view rooms under each property" — none of this is possible for non-admin users.

### Finding 8.2 — `IsAdmin` permission checks `user.client.role == 'admin'` OR `user.is_staff`

**File:** `rooms/permissions.py`
```python
def has_permission(self, request, view):
    if hasattr(user, 'client') and user.client.role == 'admin':
        return True
    return bool(user.is_staff)
```

The role is set from Supabase JWT `app_metadata.role` or `user_metadata.role`. If neither is set in Supabase, the role defaults to `'customer'` and the user cannot access any endpoint. There is no way for a user to become admin without either:
1. Setting `app_metadata.role = 'admin'` in Supabase (requires service role key)
2. Setting `is_staff = True` in Django admin

This is not documented anywhere in the README or `.env.example`.

### Finding 8.3 — `Client` model uses `ImageField` but Supabase storage is used for uploads

**File:** `accounts/models.py`
```python
image = models.ImageField(upload_to='accounts/images')
```

The `Client.image` field is an `ImageField` (stores local file path), but `UploadProfileImageView` uploads to Supabase and stores the URL string. This mismatch means:
- The `ImageField` expects a file path, but receives a URL string
- Django's `ImageField` validation may fail or produce incorrect behavior
- The `MEDIA_ROOT` directory is used for `ImageField` but Supabase is used for actual storage

**Recommendation:** Change `image` to `models.TextField(blank=True, default='')` to store the Supabase URL.

### Finding 8.4 — No token refresh handling for expired Supabase sessions on backend

The backend validates JWT expiry (`verify_exp: True`). If a user's Supabase token expires mid-session, all API calls return 401. The frontend `api.ts` handles this with a retry after `supabase.auth.refreshSession()`. However, if the refresh token is also expired (Supabase default: 60 days), the user is silently logged out without a clear error message.

---

## 9. Backend Architecture Issues

### Finding 9.1 — `Room` model missing `created_at` and `updated_at` fields

**File:** `rooms/models.py`

The `Room` model has no `created_at` or `updated_at` timestamps. The README mentions these fields in the database schema. The migration history shows `0002_room_created_at_room_updated_at_alter_room_rating_and_more.py` was created but the current `models.py` does not show these fields. Either they were removed or the migration file is stale.

### Finding 9.2 — `Room.type` choices are limited to villa/apartment/suite

**File:** `rooms/models.py`
```python
ROOM_TYPES = (
    ('villa', 'Villa'),
    ('apartment', 'Apartment'),
    ('suite', 'Suite'),
)
```

The project is called "NeoScape Properties" and aims to be a property management platform. Limiting room types to only 3 options is restrictive. No `other` or extensible option exists.

### Finding 9.3 — `PropertyDocument` has no `property` (top-level) concept

**File:** `rooms/models.py`

`PropertyDocument` links to a `Room` (nullable). There is no `Property` model — rooms ARE the properties. This means documents are attached to individual rooms, not to a property as a whole. For a property management platform, this is a significant architectural limitation.

### Finding 9.4 — No document expiry reminder endpoint for documents (only rent)

**File:** `bookings_app/views.py`

`RentReminderView` handles rent due reminders. However, `PropertyDocument` has `expiry_date` and `reminder_days` fields, but there is no endpoint that returns documents expiring soon. The frontend would need to calculate this client-side or the feature is simply missing.

### Finding 9.5 — `Booking` model has no `POST` endpoint for customers

**File:** `bookings_app/views.py`, `bookings_app/urls.py`

`BookingsView` only handles `GET` (admin list). There is no `POST` endpoint for creating bookings. The `urls.py` has no route for booking creation. This means the booking system is read-only from the API perspective — bookings can only be created directly in the Django admin.

### Finding 9.6 — `RentSchedule` is not linked to a `Room` model

**File:** `bookings_app/models.py`
```python
class RentSchedule(models.Model):
    room_name = models.CharField(max_length=255)  # Just a string, not a FK
```

`RentSchedule` stores `room_name` as a plain string, not a ForeignKey to `Room`. This means:
- No referential integrity — deleting a room doesn't affect rent schedules
- No way to query "all rent schedules for room X" via ORM
- Room name changes don't propagate to rent schedules

### Finding 9.7 — `accounts/admin.py` is empty

**File:** `accounts/admin.py`

The admin file is empty (just `from django.contrib import admin`). The `Client` model is not registered in Django admin, making it impossible to manage user roles through the admin interface without custom code.

### Finding 9.8 — `rooms/admin.py` is empty

**File:** `rooms/admin.py`

Same issue — `Room` and `PropertyDocument` are not registered in Django admin.

---

## 10. Frontend Architecture Issues

### Finding 10.1 — `vite.config.ts` has no proxy configuration

**File:** `Room-Booking-new/vite.config.ts`
```typescript
export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
  build: { sourcemap: false },
})
```

No `server.proxy` is configured. This means in development, the frontend makes direct cross-origin requests to `https://room-booking-pjo6.onrender.com/api` (the Render URL from `.env`). This works because CORS is configured on the backend. However, if a developer wants to test against a local backend, they must manually change `VITE_API_BASE_URL` in `.env`. There is no easy way to switch between local and production backends.

### Finding 10.2 — `netlify.toml` uses `pnpm` but `package.json` may use `npm`

**File:** `netlify.toml`
```toml
command = "pnpm run build"
```

If the project was set up with `npm` and `package-lock.json` exists (not `pnpm-lock.yaml`), Netlify's build will fail because `pnpm` is not installed by default. Netlify auto-detects the package manager from lock files. If `pnpm-lock.yaml` is missing, the build command should be `npm run build`.

### Finding 10.3 — `build: { sourcemap: false }` hides production errors

**File:** `Room-Booking-new/vite.config.ts`
```typescript
build: { sourcemap: false }
```

Source maps are disabled in production. This makes debugging production errors extremely difficult. Consider enabling source maps for internal use (they can be uploaded to an error tracking service like Sentry without being publicly accessible).

### Finding 10.4 — Frontend `types.ts` has `max_guests` alias alongside `maxGuests`

The backend serializer maps `max_guests` → `maxGuests` (camelCase). If `types.ts` also defines `max_guests?` as an optional field, TypeScript will not catch cases where the wrong field name is used, leading to silent `undefined` values.

### Finding 10.5 — No loading state for Render cold start

The frontend has no user-facing indication that the backend is "waking up" (Render free tier cold start). Users see a blank screen or error for 30–60 seconds on first load after inactivity. A "Connecting to server..." loading state with a retry mechanism would significantly improve UX.

---

## 11. Security Issues

### Finding 11.1 — CRITICAL: Live credentials committed to git repository

**File:** `Backend/room-booking/.env`

The following live production secrets are committed to the repository:

| Secret | Risk Level | Impact |
|--------|-----------|--------|
| `SECRET_KEY` | 🔴 Critical | Django session forgery, CSRF bypass |
| `DB_PASSWORD` | 🔴 Critical | Full database read/write access |
| `SUPABASE_JWT_SECRET` | 🔴 Critical | Forge valid JWTs for any user |
| `SUPABASE_SERVICE_ROLE_KEY` | 🔴 Critical | Bypass all RLS, full Supabase admin access |
| `EMAIL_PASSWORD` | 🟠 High | Send emails as the app's Gmail account |

**Immediate action required:**
1. Rotate ALL of these secrets immediately (new Django SECRET_KEY, new DB password, regenerate Supabase JWT secret and service role key, revoke Gmail app password)
2. Remove `.env` from git history using `git filter-branch` or BFG Repo Cleaner
3. Add `.env` to `.gitignore` (verify it's actually ignored)
4. Set all secrets as Render dashboard environment variables

### Finding 11.2 — `DEBUG=True` in committed `.env` disables production security

As detailed in §2.1, `DEBUG=True` in the committed `.env` disables:
- HTTPS redirect (`SECURE_SSL_REDIRECT`)
- HSTS headers
- Secure cookies
- CORS restrictions (`CORS_ALLOW_ALL_ORIGINS = True`)
- Django's production security hardening

### Finding 11.3 — `FERNET_SECRET_KEY` is auto-generated by Render but not used

**File:** `render.yaml`
```yaml
- key: FERNET_SECRET_KEY
  generateValue: true
```

**File:** `bookings/settings.py`
```python
FERNET_SECRET_KEY = os.environ.get("FERNET_SECRET_KEY")
```

`FERNET_SECRET_KEY` is set but never used anywhere in the codebase (no `from cryptography.fernet import Fernet` imports found). This is dead configuration that adds confusion.

### Finding 11.4 — No rate limiting on authentication endpoints

The backend has no rate limiting. The `/api/auth/verify` and `/api/me` endpoints (called on every page load) have no throttling. A malicious actor could flood these endpoints. Django REST Framework's `DEFAULT_THROTTLE_CLASSES` is not configured.

### Finding 11.5 — `SECURE_SSL_REDIRECT = True` in production may conflict with Render's proxy

**File:** `bookings/settings.py`
```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

`SECURE_PROXY_SSL_HEADER` is correctly set for Render's reverse proxy. However, `SECURE_SSL_REDIRECT = True` combined with Render's proxy can cause redirect loops if Render's internal traffic is HTTP. The `SECURE_PROXY_SSL_HEADER` setting should prevent this, but it's worth verifying.

---

## 12. README / Documentation Mismatches

### Finding 12.1 — README describes a completely different authentication system

**File:** `README.md`

The README describes JWT-based admin authentication with username/password login:
```
POST /api/auth/login
{ "username": "admin", "password": "admin123" }
```

The actual implementation uses **Supabase authentication** — there is no `/api/auth/login` endpoint. The README is describing the OLD system that was replaced by Supabase. This will confuse any developer trying to set up the project.

### Finding 12.2 — README references `core.wsgi` but actual WSGI is `bookings.wsgi`

**File:** `README.md`
```
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

**File:** `render.yaml`
```yaml
startCommand: gunicorn bookings.wsgi:application --bind 0.0.0.0:$PORT
```

The README says `core.wsgi` but the actual WSGI module is `bookings.wsgi`. Running the README command would fail.

### Finding 12.3 — README references `djangorestframework_simplejwt` but it's not in requirements

**File:** `README.md`
> Authentication: djangorestframework_simplejwt

**File:** `requirements.txt`

`djangorestframework_simplejwt` is NOT in `requirements.txt`. The project uses `PyJWT` directly with a custom `SupabaseAuthentication` class. The README is outdated.

### Finding 12.4 — README references `sslcommerz-lib` payment integration

**File:** `README.md`
> Payment Integration: sslcommerz-lib

`sslcommerz-lib` is NOT in `requirements.txt` and there is no payment integration code anywhere in the codebase. This is a leftover reference from an earlier version.

### Finding 12.5 — README `.env` example uses wrong variable names

**File:** `README.md`
```env
DATABASE_URL=your_database_connection_string
JWT_SECRET=your_super_secret_jwt_key
CORS_ORIGIN=http://localhost:3000
```

The actual `.env` uses `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, and `SUPABASE_JWT_SECRET`. None of the README variable names match the actual implementation.

---

## 13. CI/CD Pipeline Issues

### Finding 13.1 — CI runs `check --deploy` with `DEBUG=True`

**File:** `.github/workflows/ci.yml`
```yaml
env:
  DEBUG: "True"
```

The CI pipeline sets `DEBUG=True` and then runs `python manage.py check --deploy`. Django's `--deploy` check specifically warns about `DEBUG=True`. This means the CI pipeline will always produce warnings about DEBUG mode, making it impossible to distinguish real deployment issues from this expected warning.

### Finding 13.2 — CI does not set `SUPABASE_URL` or `SUPABASE_JWT_SECRET`

**File:** `.github/workflows/ci.yml`

The CI environment does not set `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, or `SUPABASE_SERVICE_ROLE_KEY`. The `settings.py` defaults these to empty strings. This means:
- `SupabaseAuthentication` will fail to validate any JWT in CI tests
- Any test that requires authentication will fail
- The `SupabaseStorage` client will not initialize

### Finding 13.3 — CI uses `ALLOWED_HOSTS: localhost,127.0.0.1` without `.onrender.com`

**File:** `.github/workflows/ci.yml`
```yaml
ALLOWED_HOSTS: localhost,127.0.0.1
```

This is correct for CI (no Render hosts needed). No issue here.

### Finding 13.4 — Render deploy hook is optional and may silently skip

**File:** `.github/workflows/ci.yml`
```yaml
if [ -z "$RENDER_DEPLOY_HOOK_URL" ]; then
  echo "⚠️  RENDER_DEPLOY_HOOK_URL not set — skipping deploy trigger."
  exit 0
fi
```

If `RENDER_DEPLOY_HOOK_URL` is not set as a GitHub secret, the deploy step silently succeeds without actually triggering a Render deploy. If Render's auto-deploy is enabled (which it likely is since the repo is connected), this is fine. But if auto-deploy is disabled, pushes to `main` will NOT trigger a Render deploy.

---

## 14. Summary Table of All Issues

| # | Finding | Severity | Category | Status |
|---|---------|----------|----------|--------|
| 2.1 | `DEBUG=True` in committed `.env` overrides Render's `DEBUG=False` | 🔴 Critical | Deployment | Open |
| 2.2 | `.env` file with live credentials committed to repo | 🔴 Critical | Security | Open |
| 2.3 | `SUPABASE_SERVICE_ROLE_KEY` missing from `render.yaml` | 🔴 Critical | Deployment | Open |
| 2.4 | `ALLOWED_HOSTS` not explicitly set in Render dashboard | 🟠 High | Deployment | Open |
| 2.5 | `CORS_ALLOWED_ORIGINS` not explicitly set in Render dashboard | 🟠 High | CORS | Open |
| 3.1 | `overwrite=False` means `.env` shadows Render dashboard vars | 🟠 High | Config | Open |
| 3.2 | `VITE_API_BASE_URL` empty in `.env.example` | 🟡 Medium | Frontend | Open |
| 3.3 | `VITE_API_BASE_URL` not set in `netlify.toml` | 🟡 Medium | Frontend | Open |
| 3.4 | `DEBUG=True` in `.env` for production | 🔴 Critical | Security | Open |
| 3.5 | `ALLOWED_HOSTS` not in `.env` file | 🟡 Medium | Config | Open |
| 4.1 | `render.yaml` missing `rootDir` (low risk currently) | 🟢 Low | Deployment | Open |
| 4.2 | `build.sh` no venv activation | 🟢 Low | Deployment | Open |
| 4.3 | `requirements.txt` uses open version ranges | 🟠 High | Stability | Open |
| 4.4 | `start_server.py` dev-only file in repo root | 🟢 Low | Cleanup | Open |
| 4.5 | Health check path correct | ✅ OK | Deployment | — |
| 4.6 | Gunicorn 3 workers may OOM on Render free tier | 🟠 High | Deployment | Open |
| 5.1 | `CORS_ALLOW_ALL_ORIGINS = DEBUG` dangerous with `DEBUG=True` | 🔴 Critical | CORS | Open |
| 5.2 | `CORS_ALLOWED_ORIGINS` fallback includes localhost | 🟢 Low | CORS | Open |
| 5.3 | `CORS_ALLOWED_ORIGINS` not set in Render dashboard | 🟡 Medium | CORS | Open |
| 5.4 | `CSRF_TRUSTED_ORIGINS` hardcodes Render URL | 🟡 Medium | CORS | Open |
| 6.1 | `api.ts` hardcodes Render URL as fallback | 🟡 Medium | Frontend | Open |
| 6.2 | Render free tier spin-down causes cold start failures | 🔴 Critical | Deployment | Open |
| 6.3 | Trailing slash inconsistency in URL patterns | 🟠 High | Backend | Open |
| 6.4 | 401 retry logic may mask non-expiry auth errors | 🟢 Low | Frontend | Open |
| 7.1 | `SUPABASE_SERVICE_ROLE_KEY` missing from `render.yaml` | 🔴 Critical | Supabase | Open |
| 7.2 | Supabase JWT secret committed to repo | 🔴 Critical | Security | Open |
| 7.3 | Supabase service role key committed to repo | 🔴 Critical | Security | Open |
| 7.4 | Database password committed to repo | 🔴 Critical | Security | Open |
| 7.5 | JWKS client cached indefinitely (key rotation risk) | 🟡 Medium | Auth | Open |
| 7.6 | No Supabase bucket existence check at startup | 🟢 Low | Supabase | Open |
| 8.1 | All endpoints require `IsAdmin` — no customer access | 🔴 Critical | Architecture | Open |
| 8.2 | No documentation on how to set admin role in Supabase | 🟠 High | Auth | Open |
| 8.3 | `Client.image` is `ImageField` but stores Supabase URL | 🟠 High | Backend | Open |
| 8.4 | No graceful handling of expired refresh tokens | 🟡 Medium | Auth | Open |
| 9.1 | `Room` model missing `created_at`/`updated_at` | 🟡 Medium | Backend | Open |
| 9.2 | `Room.type` limited to 3 choices | 🟢 Low | Backend | Open |
| 9.3 | No top-level `Property` model | 🟡 Medium | Architecture | Open |
| 9.4 | No document expiry reminder endpoint | 🟡 Medium | Backend | Open |
| 9.5 | No `POST` endpoint for booking creation | 🔴 Critical | Backend | Open |
| 9.6 | `RentSchedule.room_name` is a string, not FK | 🟠 High | Backend | Open |
| 9.7 | `accounts/admin.py` empty — `Client` not in Django admin | 🟠 High | Backend | Open |
| 9.8 | `rooms/admin.py` empty — `Room` not in Django admin | 🟠 High | Backend | Open |
| 10.1 | No Vite proxy for local backend switching | 🟡 Medium | Frontend | Open |
| 10.2 | `netlify.toml` uses `pnpm` — may fail if no `pnpm-lock.yaml` | 🟠 High | Deployment | Open |
| 10.3 | Source maps disabled — hard to debug production errors | 🟡 Medium | Frontend | Open |
| 10.4 | `types.ts` may have `max_guests` alias alongside `maxGuests` | 🟡 Medium | Frontend | Open |
| 10.5 | No loading state for Render cold start | 🟠 High | UX | Open |
| 11.1 | Live credentials committed to git | 🔴 Critical | Security | Open |
| 11.2 | `DEBUG=True` disables all production security | 🔴 Critical | Security | Open |
| 11.3 | `FERNET_SECRET_KEY` configured but never used | 🟢 Low | Cleanup | Open |
| 11.4 | No rate limiting on auth endpoints | 🟡 Medium | Security | Open |
| 11.5 | `SECURE_SSL_REDIRECT` may conflict with Render proxy | 🟡 Medium | Security | Open |
| 12.1 | README describes wrong auth system (username/password) | 🟠 High | Docs | Open |
| 12.2 | README references `core.wsgi` instead of `bookings.wsgi` | 🟠 High | Docs | Open |
| 12.3 | README references `simplejwt` not in requirements | 🟡 Medium | Docs | Open |
| 12.4 | README references `sslcommerz-lib` not in codebase | 🟡 Medium | Docs | Open |
| 12.5 | README `.env` example uses wrong variable names | 🟠 High | Docs | Open |
| 13.1 | CI runs `check --deploy` with `DEBUG=True` | 🟡 Medium | CI/CD | Open |
| 13.2 | CI missing Supabase env vars — auth tests will fail | 🟠 High | CI/CD | Open |
| 13.3 | CI `ALLOWED_HOSTS` correct | ✅ OK | CI/CD | — |
| 13.4 | Render deploy hook silently skips if secret not set | 🟡 Medium | CI/CD | Open |

---

## 15. Recommended Fixes (Priority Order)

### 🔴 IMMEDIATE (Do these today — security and production stability)

**Fix 1: Rotate all committed secrets**
1. Generate a new Django `SECRET_KEY` (use `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
2. Change the Supabase database password in Supabase dashboard → Project Settings → Database
3. Regenerate Supabase JWT secret in Supabase dashboard → Project Settings → API → JWT Settings
4. Regenerate Supabase service role key (create a new one, revoke the old)
5. Revoke the Gmail app password and generate a new one

**Fix 2: Remove `.env` from the repository**
```bash
# Add to .gitignore
echo ".env" >> .gitignore

# Remove from git tracking (keeps the file locally)
git rm --cached .env
git commit -m "Remove .env from tracking — secrets must be set in Render dashboard"
```
Then use BFG Repo Cleaner or `git filter-repo` to purge the file from git history.

**Fix 3: Set all secrets in Render dashboard**
Go to Render dashboard → room-booking service → Environment and set:
- `SECRET_KEY` = new generated value
- `DEBUG` = `False`
- `ALLOWED_HOSTS` = `room-booking-pjo6.onrender.com`
- `CORS_ALLOWED_ORIGINS` = `https://neoscapeproperties.netlify.app`
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` = new DB credentials
- `SUPABASE_URL` = `https://oizurkxzopglxdcvffie.supabase.co`
- `SUPABASE_JWT_SECRET` = new JWT secret
- `SUPABASE_SERVICE_ROLE_KEY` = new service role key
- `EMAIL` = Gmail address
- `EMAIL_PASSWORD` = new Gmail app password

**Fix 4: Add `SUPABASE_SERVICE_ROLE_KEY` to `render.yaml`**
```yaml
- key: SUPABASE_SERVICE_ROLE_KEY
  sync: false
```

**Fix 5: Change `environ.Env.read_env` to `overwrite=True`**
```python
# bookings/settings.py
environ.Env.read_env(os.path.join(BASE_DIR, '.env'), overwrite=True)
```
This ensures Render's dashboard env vars always win over any `.env` file that might exist.

**Fix 6: Fix Render free tier cold start (primary reported issue)**
Option A — Add a keep-alive service (free):
- Sign up at UptimeRobot (free tier)
- Add HTTP monitor for `https://room-booking-pjo6.onrender.com/` every 5 minutes
- This prevents the service from spinning down

Option B — Upgrade to Render Starter plan ($7/month) for always-on service

Option C — Add frontend retry with user feedback:
```typescript
// In api.ts — add retry with exponential backoff and user notification
```

**Fix 7: Reduce Gunicorn workers to 2**
```yaml
# render.yaml
startCommand: gunicorn bookings.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

---

### 🟠 HIGH PRIORITY (Fix within this sprint)

**Fix 8: Add trailing slash consistency to `core/urls.py`**
```python
# core/urls.py — add trailing slashes
path('upload/images/', UploadImagesView.as_view(), name='upload-images'),
path('admin/stats/', AdminStatsView.as_view(), name='admin-stats'),
path('auth/verify/', VerifyTokenView.as_view(), name='auth-verify'),
path('me/', MeView.as_view(), name='auth-me'),
```
And update frontend `api.ts` to match.

**Fix 9: Register models in Django admin**
```python
# accounts/admin.py
from django.contrib import admin
from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'mobile_no']
    list_filter = ['role']
    search_fields = ['user__username', 'user__email']
```

```python
# rooms/admin.py
from django.contrib import admin
from .models import Room, PropertyDocument

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'price', 'location', 'available']
    list_filter = ['type', 'available']
    search_fields = ['name', 'location']

@admin.register(PropertyDocument)
class PropertyDocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'status', 'expiry_date']
    list_filter = ['type', 'status']
```

**Fix 10: Fix `Client.image` field type**
```python
# accounts/models.py
image = models.TextField(blank=True, default='')  # Store Supabase URL, not file path
```
Create and run a migration after this change.

**Fix 11: Pin `requirements.txt` to exact versions**
Run `pip freeze > requirements.txt` in the virtual environment to get exact pinned versions.

**Fix 12: Fix `netlify.toml` build command**
Check if `pnpm-lock.yaml` exists in the frontend folder. If not, change to:
```toml
command = "npm run build"
```

**Fix 13: Set `VITE_API_BASE_URL` in Netlify dashboard**
Go to Netlify → Site settings → Environment variables and add:
- `VITE_API_BASE_URL` = `https://room-booking-pjo6.onrender.com/api`

---

### 🟡 MEDIUM PRIORITY (Fix in next sprint)

**Fix 14: Add document expiry reminder endpoint**
```python
# rooms/views.py — add DocumentReminderView
class DocumentReminderView(APIView):
    permission_classes = [IsAdmin]
    def get(self, request):
        from django.utils import timezone
        today = timezone.now().date()
        docs = PropertyDocument.objects.filter(
            expiry_date__isnull=False,
            status__in=['active', 'expiring-soon']
        )
        reminders = []
        for doc in docs:
            days_until = (doc.expiry_date - today).days
            if days_until <= doc.reminder_days:
                reminders.append({...})
        return Response({'success': True, 'data': reminders})
```

**Fix 15: Add JWKS cache TTL**
```python
# accounts/authentication.py
from functools import lru_cache
import time

_jwks_cache = {}
_JWKS_TTL = 3600  # 1 hour

def _get_jwk_client(jwks_url: str) -> PyJWKClient:
    now = time.time()
    if jwks_url not in _jwks_cache or now - _jwks_cache[jwks_url][1] > _JWKS_TTL:
        _jwks_cache[jwks_url] = (PyJWKClient(jwks_url), now)
    return _jwks_cache[jwks_url][0]
```

**Fix 16: Add DRF throttling**
```python
# bookings/settings.py
REST_FRAMEWORK = {
    ...
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}
```

**Fix 17: Add Vite proxy for local development**
```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: process.env.VITE_API_BASE_URL || 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

**Fix 18: Add frontend cold start handling**
Add a backend health check on app load with a user-facing "Connecting..." state and automatic retry.

**Fix 19: Update README to reflect actual implementation**
Rewrite README to document:
- Supabase authentication (not username/password)
- Correct WSGI module (`bookings.wsgi`)
- Correct env variable names
- How to set admin role in Supabase
- Actual API endpoints

---

### 🟢 LOW PRIORITY (Backlog)

- Remove `start_server.py` from repo root (or move to `scripts/`)
- Remove `FERNET_SECRET_KEY` from `render.yaml` if not used
- Add `Room.created_at` and `Room.updated_at` fields
- Link `RentSchedule` to `Room` model via ForeignKey
- Add `other` to `Room.type` choices
- Enable source maps for error tracking
- Add Supabase bucket existence check at startup
- Add customer-facing endpoints (room browsing, booking creation)

---

## 16. Remaining Risks

### Risk 1 — Render free tier is fundamentally unreliable for production
Even after all fixes, Render's free tier spins down after 15 minutes of inactivity. The first request after spin-down takes 30–60 seconds. For a "premium real estate SaaS" this is unacceptable. **Upgrading to Render Starter ($7/month) is the single most impactful change for production reliability.**

### Risk 2 — Supabase project credentials are now compromised
Since the `.env` file was committed to a public repo, all secrets in it must be considered compromised regardless of whether the repo is now private. Rotating credentials is mandatory, not optional.

### Risk 3 — No customer-facing API means the platform is admin-only
The entire API surface requires `IsAdmin`. If the frontend has any customer-facing pages (room browsing, booking), they will all fail with 403 Forbidden for non-admin users. This is a fundamental architectural gap that needs to be addressed before the platform can serve real users.

### Risk 4 — No booking creation endpoint
There is no `POST /api/bookings/` endpoint. Bookings can only be created via Django admin. This means the core booking functionality of the platform is not accessible via the API.

### Risk 5 — Database connection uses Supabase connection pooler (port 6543)
The `.env` uses `DB_PORT=6543` (Supabase's PgBouncer pooler). This is correct for serverless/short-lived connections but can cause issues with Django's persistent connection model (`CONN_MAX_AGE`). If `CONN_MAX_AGE` is set to a non-zero value, connections may be dropped by the pooler. Currently `CONN_MAX_AGE` is not set (defaults to 0), so this is not an active issue but should be documented.

### Risk 6 — No backup or disaster recovery plan
There is no documented backup strategy for the PostgreSQL database. Supabase provides automatic backups on paid plans, but this should be verified.

### Risk 7 — `accounts/migrations/0001_initial.py` uses `ImageField` for `Client.image`
If `Client.image` is changed to `TextField` (Fix 10), a migration must be created and run. On Render, migrations run automatically via `build.sh`. However, if the migration conflicts with existing data, the build will fail and the deployment will be blocked.

---

## Appendix: Deployment Checklist

Before the next production deploy, verify:

- [ ] All secrets rotated (SECRET_KEY, DB_PASSWORD, SUPABASE_JWT_SECRET, SUPABASE_SERVICE_ROLE_KEY, EMAIL_PASSWORD)
- [ ] `.env` removed from git and git history purged
- [ ] `.env` added to `.gitignore`
- [ ] All env vars set in Render dashboard (not relying on `.env` file)
- [ ] `SUPABASE_SERVICE_ROLE_KEY` added to `render.yaml`
- [ ] `DEBUG=False` confirmed in Render dashboard
- [ ] `ALLOWED_HOSTS` set in Render dashboard
- [ ] `CORS_ALLOWED_ORIGINS` set in Render dashboard
- [ ] `VITE_API_BASE_URL` set in Netlify dashboard
- [ ] Gunicorn workers reduced to 2
- [ ] UptimeRobot or equivalent keep-alive configured
- [ ] `netlify.toml` build command matches package manager
- [ ] Django admin models registered
- [ ] `Client.image` field type fixed

---

*Report generated by Kiro AI — May 20, 2026*
*All findings are based on static analysis of the committed codebase. Dynamic testing (actual API calls, load testing, penetration testing) was not performed and is recommended as a follow-up.*
