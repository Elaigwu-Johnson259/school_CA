# Phase 3 — Authentication & User Accounts — CHANGELOG

Builds directly on the existing Phase 1 (project setup) + Phase 2
(database models) codebase. Nothing was redesigned, restarted, or
replaced.

## Files added

**Backend**
- `backend/app/core/security.py` — password hashing (`hash_password`,
  `verify_password`) and JWT helpers (`create_access_token`,
  `create_refresh_token`, `decode_token`).
- `backend/app/models/auth.py` — new `RefreshToken` model (for logout /
  revocation).
- `backend/app/schemas/auth.py` — `LoginRequest`, `TokenResponse`,
  `AccessTokenResponse`, `RefreshRequest`, `LogoutRequest`.
- `backend/app/services/auth_service.py` — `authenticate_user`,
  `issue_tokens`, `get_valid_refresh_token`, `revoke_refresh_token`,
  `create_user`.
- `backend/app/api/deps.py` — `get_current_user()`, `require_roles(...)`.
- `backend/app/api/auth.py` — the `/api/auth/*` router.
- `backend/alembic/versions/4dc4f1df9355_add_refresh_tokens_table.py` —
  migration adding the `refresh_tokens` table.
- `backend/tests/test_security.py` — password hashing + JWT unit tests.
- `backend/tests/test_auth_api.py` — end-to-end tests for the `/api/auth/*`
  endpoints.
- `backend/tests/test_authorization.py` — unit tests for `require_roles`.

**Frontend**
- `frontend/src/types/auth.ts` — shared auth types.
- `frontend/src/api/auth.ts` — `login`, `fetchCurrentUser`,
  `refreshAccessToken`, `logout` API calls.
- `frontend/src/utils/tokenStorage.ts` — localStorage token helpers.
- `frontend/src/context/AuthContext.tsx` — auth state + `login`/`logout`.
- `frontend/src/routes/ProtectedRoute.tsx` — redirects unauthenticated
  users to `/login`.
- `frontend/src/pages/LoginPage.tsx` — login form.
- `frontend/src/pages/DashboardPage.tsx` — minimal authenticated page
  (shows user email/role, log-out button).

## Files modified

- `backend/app/core/database.py` — enabled `PRAGMA foreign_keys=ON` and
  `check_same_thread=False` for SQLite (added in Phase 2, unchanged this
  phase).
- `backend/app/models/__init__.py` — registered the new `RefreshToken`
  model.
- `backend/alembic/env.py` — imports `RefreshToken` alongside the existing
  Phase 2 model imports.
- `backend/app/main.py` — added `app.include_router(auth_router)`. The
  `/api/health` route itself is untouched — same code, same response.
- `backend/requirements.txt` — see "New dependencies" below.
- `backend/tests/conftest.py` — added a `client` fixture (a `TestClient`
  wired to the same in-memory `db_session` used by the existing Phase 2
  tests) and default env vars for `DATABASE_URL`/`JWT_SECRET` so `pytest`
  works without requiring a `.env` file. The existing `db_session` fixture
  is untouched.
- `frontend/src/api/client.ts` — added request/response interceptors:
  attach the access token to outgoing requests, and on a 401 try one
  silent refresh-and-retry.
- `frontend/src/App.tsx` — replaced the Phase 1 health-check placeholder
  with real routing (`/login`, `/dashboard`, wrapped in `AuthProvider`).
- `README.md` — added the "Phase 3 — Authentication" section.

## Database changes

One new table, `refresh_tokens` (id, user_id → users.id, jti (unique),
expires_at, revoked, created_at, updated_at). No existing Phase 2 tables
were altered. Migration is reversible
(`alembic downgrade -1` / `alembic upgrade head` both verified).

## New API endpoints

- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`

## New frontend features

Login page → authenticated state (React context) → protected route →
minimal dashboard showing the logged-in user → logout. Axios client
automatically attaches access tokens and retries once via refresh on 401.

## New dependencies

- **Backend:** `bcrypt==4.0.1` pinned explicitly (passlib 1.7.4, already
  in Phase 1's `requirements.txt`, is incompatible with bcrypt ≥ 4.1).
  `python-jose[cryptography]` and `passlib[bcrypt]` were already present
  in Phase 1's `requirements.txt` and are simply put to use here — no new
  entry needed for either.
- **Frontend:** none — `axios` and `react-router-dom` were already
  dependencies from Phase 1.

## Test results

```
28 passed
```

- 14 pre-existing tests (1 health check + 6 Phase 2 model tests, run
  unmodified) — all still pass.
- 14 new Phase 3 tests: password hashing/verification, JWT claim/expiry
  checks, login (success/wrong password/unknown email/inactive user),
  `/api/auth/me` (authenticated + unauthenticated), invalid/expired token
  rejection, refresh token issuing a new access token, access token
  rejected when used as a refresh token, logout revoking a refresh token,
  and `require_roles` allow/deny behavior.

Frontend: `npm run build` completes cleanly (TypeScript + Vite, no errors
or warnings).

## Verified before packaging

- `alembic upgrade head` applies cleanly to a fresh SQLite database
  (`sqlite:///./school_results.db`), producing 18 tables total (17 from
  Phase 2 + `refresh_tokens`).
- `alembic downgrade -1` / `alembic upgrade head` round-trip cleanly.
- `GET /api/health` still returns `{"status": "ok", "environment":
  "development"}` — unchanged from Phase 1.
- No Docker, no PostgreSQL required anywhere in this phase.
