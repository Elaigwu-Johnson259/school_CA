# School Results Management System

A production-oriented, multi-tenant Student CA / Examination / Results /
Report Management web application. Multiple independent schools use the
same platform, each with its own fully isolated data.

This README covers **Phase 1 — Project Setup** only. It will be updated as
each later phase (database, auth, multi-tenancy, results engine, etc.) is
built.

## Stack

- **Frontend:** React + TypeScript + Vite + Tailwind CSS + React Router +
  TanStack Query + React Hook Form + Zod
- **Backend:** Python + FastAPI + SQLAlchemy + Alembic + Pydantic
- **Database:** PostgreSQL
- **Auth:** JWT-based (added in Phase 3)

## Project layout

```text
school-results-management/
├── frontend/         React/TS/Vite app
│   └── src/
│       ├── api/       axios client + typed API calls
│       ├── components/ reusable UI pieces
│       ├── pages/      route-level screens (added later phases)
│       ├── layouts/    shared page shells (sidebar, topbar, etc.)
│       ├── hooks/      custom React hooks
│       ├── services/   frontend-side business helpers
│       ├── types/      shared TypeScript types
│       └── utils/      small helper functions
├── backend/          FastAPI app
│   └── app/
│       ├── api/          route handlers, grouped by feature
│       ├── core/         config, DB session, security helpers
│       ├── models/       SQLAlchemy ORM models (Phase 2)
│       ├── schemas/      Pydantic request/response schemas
│       ├── services/     business logic (e.g. ResultCalculationService)
│       ├── repositories/ database query layer
│       ├── middleware/   tenant isolation, auth checks
│       └── utils/        small helper functions
├── docs/             architecture & process notes
├── docker-compose.yml
└── .env.example
```

## What each backend folder is for (plain-language)

- **core/** — the "plumbing": reads environment variables (`config.py`) and
  sets up the database connection (`database.py`). Nothing school-specific
  lives here.
- **models/** — the shape of your database tables in Python (one class per
  table). Empty until Phase 2.
- **schemas/** — the shape of API requests/responses. Similar to models,
  but these describe what goes over the network, not what's in the
  database — keeping the two separate is what lets you change your API
  without breaking your database, and vice versa.
- **services/** — where real business logic lives (e.g. calculating a
  student's average or position). Keeping this separate from `api/` means
  the calculation logic can be tested on its own, without needing a live
  HTTP request.
- **repositories/** — functions that actually query the database, so
  services don't need to know SQLAlchemy details directly.
- **middleware/** — code that runs on *every* request, such as checking
  that a logged-in user's `school_id` matches the resource they're asking
  for (multi-tenant isolation).

## Running it

### Option A — Docker (recommended once you have Docker installed)

```bash
cp .env.example .env
docker compose up --build
```

- Backend: http://localhost:8000/api/health
- Frontend: http://localhost:5173

### Option B — Running natively

**Backend:**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env      # then edit DATABASE_URL if not using Docker's Postgres
uvicorn app.main:app --reload
```

Visit http://localhost:8000/api/health — you should see:

```json
{"status": "ok", "environment": "development"}
```

**Frontend** (in a second terminal):

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173 — you should see a page confirming the backend
health check succeeded.

> Note: the frontend expects the backend to be running at
> `http://localhost:8000/api` (set via `VITE_API_BASE_URL` in `.env`).

### Testing what's been built so far

```bash
cd backend
source venv/bin/activate
pip install pytest httpx
pytest
```

This currently runs one test proving the FastAPI app boots and the health
endpoint responds correctly.

## What was built in Phase 1

- Repository structure for `frontend/` and `backend/`, matching the target
  architecture.
- A working FastAPI app with CORS configured and a `/api/health` endpoint.
- A working Vite + React + TypeScript + Tailwind frontend that calls the
  backend's health endpoint and displays the result.
- `docker-compose.yml` wiring together Postgres, the backend, and the
  frontend.
- `.env.example` documenting every environment variable the app needs.
- A first backend test (`backend/tests/test_health.py`).

Both the backend (`pytest`) and frontend (`npm run build`) were verified to
install and run successfully in this environment.

## What remains

Everything else in the spec — database models, authentication, tenant
isolation, school/student/teacher management, the assessment and result
calculation engine, the result approval workflow, the student portal,
report card/PDF generation, dashboards, audit logging, and full test
coverage — comes in Phases 2 onward, one phase at a time, with a check-in
after each.

## Phase 2 — Database (complete)

Added the full set of SQLAlchemy models (17 tables) covering schools,
users, academic sessions/terms, classes/subjects, teachers/students and
their assignments, the configurable assessment structure, scores, grading
scales, calculated results, report cards, and audit logs — plus matching
Pydantic schemas for the core entities, an Alembic migration that creates
them all, and a test suite proving the relationships and tenant-scoped
constraints work. See `backend/app/models/` and
`backend/tests/test_models.py`.

**Next up: Phase 3 — Authentication.**

## Phase 3 — Authentication & User Accounts (complete)

### How authentication works

- **Passwords** are hashed with bcrypt (via passlib) in
  `app/core/security.py` — `hash_password()` / `verify_password()`.
  Plain-text passwords are never stored, logged, or returned by the API.
- **Access tokens** are short-lived JWTs (`ACCESS_TOKEN_EXPIRE_MINUTES`,
  default 30 min), sent as `Authorization: Bearer <token>` on every
  authenticated request. They're stateless — nothing to check in the DB —
  which keeps normal request handling fast.
- **Refresh tokens** are longer-lived JWTs (`REFRESH_TOKEN_EXPIRE_DAYS`,
  default 7 days) used only to obtain a new access token. Each one is also
  recorded in a new `refresh_tokens` table (by its JWT `jti` claim), which
  is what makes logout/revocation possible — a stolen refresh token can be
  cut off before it naturally expires, unlike a purely stateless token.
- **`/api/auth/refresh`** checks the token's `type` claim is `"refresh"`
  (an access token is rejected), looks up its `jti` in `refresh_tokens`,
  and rejects it if it's missing, expired, or revoked.
- **`/api/auth/logout`** marks the given refresh token's `jti` as revoked.
  The paired access token is left to expire naturally (it's stateless by
  design) — the frontend discards it immediately on logout regardless.
- **`get_current_user()`** (`app/api/deps.py`) is the dependency every
  protected endpoint uses: it validates the bearer token, checks it's an
  access token, loads the user, and rejects inactive accounts.
- **`require_roles(...)`** builds on `get_current_user()` for
  role-restricted endpoints, e.g.
  `Depends(require_roles(UserRole.SCHOOL_ADMIN, UserRole.TEACHER))`. No
  endpoints use it yet — Phase 3 is authentication, not the endpoints that
  will need it — but it's ready for later phases to use directly.
- **Tenant awareness**: every access token carries the user's `school_id`
  claim, and `/api/auth/me` returns it too. Actually *enforcing* that a
  SCHOOL_ADMIN/TEACHER/STUDENT can only touch their own school's data is
  Phase 4's job (tenant isolation middleware); Phase 3 just makes sure
  that information is reliably available to build that on top of.

### Why there's no public registration endpoint

A public `POST /api/auth/register` would let anyone create an account —
including, if not carefully restricted, a `SUPER_ADMIN`. Instead, Phase 3
adds `auth_service.create_user()`, a plain function that hashes the
password and inserts the user. It's not wired to any route yet. Later
phases will call it from *protected* endpoints where the caller's
authorization is already established — e.g. a `SUPER_ADMIN` creating a
school + its first `SCHOOL_ADMIN` during school registration (Phase 5), or
a `SCHOOL_ADMIN` creating teacher/student accounts (Phase 6).

### Creating a development user to test with

There's no seed data yet (that's Phase 2's seed-data task, still pending,
and/or Phase 5+). Until then, create one by hand:

```bash
cd backend
source venv/bin/activate
alembic upgrade head
python -c "
from app.core.database import SessionLocal
from app.services.auth_service import create_user
from app.models.enums import UserRole

db = SessionLocal()
create_user(db, email='admin@example.com', password='ChangeMe123!', role=UserRole.SCHOOL_ADMIN)
db.close()
print('Created admin@example.com / ChangeMe123!')
"
```

(A `SCHOOL_ADMIN` needs a real `school_id` in practice — pass
`school_id=<id>` once you have a school row from Phase 2's models. For
just testing the login flow, a `SUPER_ADMIN` with no `school_id` also
works fine: `role=UserRole.SUPER_ADMIN`.)

### Authentication endpoints

| Method | Path | Auth required | Purpose |
|---|---|---|---|
| POST | `/api/auth/login` | No | Exchange email+password for an access + refresh token |
| GET | `/api/auth/me` | Yes (access token) | Return the current user's id/email/role/school_id/is_active |
| POST | `/api/auth/refresh` | No (refresh token in body) | Exchange a refresh token for a new access token |
| POST | `/api/auth/logout` | No (refresh token in body) | Revoke a refresh token |

### Frontend

- `src/context/AuthContext.tsx` — holds the current user, exposes
  `login()`/`logout()`, and re-checks `/api/auth/me` on page load if a
  token is already stored.
- `src/utils/tokenStorage.ts` — stores the access/refresh token pair in
  `localStorage`. (Trade-off note: this is simpler than httpOnly cookies
  but readable by page JS; fine for Phase 3, worth hardening later.)
- `src/api/client.ts` — attaches the access token to every request, and
  on a 401 tries one silent refresh-and-retry before giving up.
- `src/routes/ProtectedRoute.tsx` — redirects to `/login` if there's no
  authenticated user.
- `src/pages/LoginPage.tsx` / `src/pages/DashboardPage.tsx` — a minimal
  login form and a placeholder authenticated page (shows the user's
  email/role, has a log-out button). Real dashboards come in a later
  phase — this only proves login → protected page → logout works.

Try it: run both servers (below), open http://localhost:5173, you'll be
redirected to `/login`; sign in with a user you created above; you'll
land on `/dashboard` showing your email and role; click "Log out" to
return to `/login`.

### Running it

**Backend:**

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend** (second terminal):

```bash
cd frontend
npm install
npm run dev
```

**Tests:**

```bash
cd backend
source venv/bin/activate
pytest -v
```

**Next up: Phase 4 — Multi-Tenancy** (enforcing that a logged-in user can
only ever read/write their own school's data, with tests proving
cross-school access is impossible).

## Phase 4 — Multi-Tenancy & Tenant Isolation (complete)

### The tenant model

Every school-owned row (already true since Phase 2) carries a `school_id`.
A `School` **is** a tenant. The rule from Phase 2/3 continues to hold:
`SUPER_ADMIN.school_id` is `NULL` (platform-wide, no single home school);
`SCHOOL_ADMIN`/`TEACHER`/`STUDENT` each belong to exactly one school.

### Tenant-context mechanism (`backend/app/core/tenancy.py`)

- **`get_current_school()`** — a FastAPI dependency that resolves the
  logged-in user's own school from their trusted, DB-loaded `school_id`.
  Rejects `SUPER_ADMIN` with `403`, since they have no single "home"
  school by design.
- **`require_school_user()`** — ensures the caller is school-bound (i.e.
  not a `SUPER_ADMIN`), for endpoints that only make sense for one.
- **`require_school_role(*roles)`** — combines a role check with the
  "must belong to a school" check in one dependency.
- **`ensure_same_school(current_user, resource_school_id)`** — called
  after fetching a specific resource by ID; raises `404` (never `403`,
  see below) if the resource's school doesn't match the caller's, unless
  the caller is a `SUPER_ADMIN`.
- **`scope_to_school(query, model, current_user)`** — wraps a list/search
  query with the `school_id` filter for every role except `SUPER_ADMIN`.
  This is the reusable pattern later phases should use for teachers,
  students, classes, subjects, assessments, scores, results, and report
  cards, instead of each endpoint writing its own `school_id` check.

**Where tenant identity comes from:** always `current_user.school_id`, as
loaded fresh from the database inside Phase 3's `get_current_user()` — a
`school_id` claim baked into the JWT is never used for an authorization
decision, only the freshly-loaded DB row. If an admin changes a user's
school, role, or active status, that takes effect on their very next
request, not after their token happens to expire.

### Why 404 instead of 403 for cross-tenant access

When a School A user asks for School B's data by ID, the API returns the
exact same `404 Not Found` it would return for an ID that doesn't exist
at all — proven in
`test_nonexistent_school_id_and_wrong_tenant_school_id_look_identical`,
which asserts the two responses are byte-for-byte equal. A `403` would
leak "this exists, you just can't have it"; `404` doesn't.

### SUPER_ADMIN behavior

- `GET /api/schools/me` → `403` (no home school).
- `GET /api/schools/{id}` → works for **any** school ID — this is the
  "explicitly authorized Super Admin functionality" the spec calls for.
  A `SUPER_ADMIN` is never treated as implicitly belonging to every
  school through the ordinary tenant dependencies above
  (`get_current_school`/`require_school_user` both reject them); cross-
  school access only happens through an endpoint that explicitly checks
  for the `SUPER_ADMIN` role, like `get_school_by_id`.

### New endpoints

| Method | Path | Auth | Behavior |
|---|---|---|---|
| GET | `/api/schools/me` | School-bound user | Returns the caller's own school. `403` for `SUPER_ADMIN`. |
| GET | `/api/schools/{school_id}` | Any authenticated user | Own school → `200`. `SUPER_ADMIN` → any school → `200`. Anyone else's ID → `404`. |

Full school management (create/edit/logo upload/branding) is Phase 5.

### Mass-assignment protection

Checked every existing Phase 2 `*Create` schema
(`StudentCreate`, `TeacherCreate`, `SchoolClassCreate`, `SubjectCreate`,
`AcademicSessionCreate`, `AssessmentTypeCreate`, `GradingScaleCreate`,
`ScoreCreate`): **none of them accept a `school_id` field** — they never
did, going back to how they were designed in Phase 2. So there was
nothing to remove here; this phase's job was making sure that stays true
as write endpoints for those resources get built in later phases (use
`current_user.school_id` / `get_current_school()` server-side, never a
client-supplied value — see `ensure_same_school`/`scope_to_school`).

### Database migration

**No Phase 4 database migration required.** No models or columns
changed — tenant isolation here is entirely an authorization-layer
concern on top of the `school_id` columns Phase 2 already added.
Migration history is unchanged: `f98225df0d46` → `4dc4f1df9355`.

### Frontend

The dashboard (`src/pages/DashboardPage.tsx`) now calls the new
`GET /api/schools/me` (`src/api/schools.ts`) for school-bound users and
displays the school's name alongside the existing email/role display —
proving the tenant context flows through end to end, without yet being a
real dashboard. `SUPER_ADMIN` users skip that call entirely (shown as
"Platform administrator" instead), matching the backend's 403 for them.
As always, none of this is a security boundary — the backend enforces
isolation regardless of what the frontend shows or hides.

### Running the Phase 4 tests

```bash
cd backend
source venv/bin/activate
pytest -v
```

`tests/test_tenancy_unit.py` — unit tests for `ensure_same_school` and
`scope_to_school`, run directly without HTTP.
`tests/test_tenant_isolation_api.py` — full end-to-end tests: two schools,
a user in each, a `SUPER_ADMIN`, and every cross-tenant scenario from the
spec (own school access, blocked cross-school access by URL ID, identical
404s for "not yours" vs. "doesn't exist", `SUPER_ADMIN` cross-school
access, request-body `school_id` tampering ignored, unauthenticated
requests, inactive users).

### Login and identity UX

Live testing after Phase 3 surfaced two gaps, both addressed here:

1. **The login page didn't identify the product.** It now shows "School
   Results Management" with the tagline "Manage assessments, results and
   reports" above the form. The login form itself is unchanged — still
   just email + password, no role or school picker. Letting a user claim
   "I am a SCHOOL_ADMIN" or "I belong to School X" from a form would let
   them self-assign privileges; identity and tenant come only from what
   the backend already knows about the authenticated account.
2. **After logging in, it wasn't obvious which account/tenant you were
   using.** The dashboard now shows, for a school-bound user, their
   school's name, email, and a human-readable role label (`SCHOOL_ADMIN`
   → "School Administrator", `TEACHER` → "Teacher", `STUDENT` → "Student"
   — see `src/utils/roleLabels.ts`). A `SUPER_ADMIN` sees "School Results
   Management" with a "Global Administration" badge instead of a
   fabricated school — consistent with the backend never treating them as
   belonging to one.

### Login page: "Create your school account" (placeholder only)

The login page now has a "New school? Create your school account" link,
going to `/register-school`. That page is a static placeholder — no form
fields, no API call, no database writes — saying registration isn't
available yet and linking back to sign-in. The real flow (create one
School + its first SCHOOL_ADMIN) is Phase 5. This exists so the link has
somewhere honest to go rather than being a dead link, a silently-broken
form, or (worse) a real, unrestricted "pick your own role and school_id"
registration form — which Phase 4 is explicitly designed to prevent
(see "Future Phase 5 registration architecture" below).

### Future Phase 5 registration architecture (why Phase 4 doesn't block it)

Phase 5 will add self-service registration that creates **one School +
one initial SCHOOL_ADMIN** for it, using the same building blocks already
in place:

- `auth_service.create_user()` (Phase 3) already hashes the password and
  inserts a `User` row with whatever `role`/`school_id` its caller passes
  — a future registration endpoint calls it with a freshly-created
  `School.id` and `role=UserRole.SCHOOL_ADMIN`, not values the client
  supplied.
- Nothing in Phase 4 lets a client choose their own role or `school_id`
  anywhere (`/api/schools/me` and `/api/schools/{id}` are both read-only
  and both derive identity from the authenticated user, never from the
  request). A future public registration endpoint follows the identical
  rule: it may create a school + its first admin, but it must never
  accept a client-supplied `role` or `school_id` for that admin, and it
  must never let someone attach themselves to an *existing* school.
  Teacher/student account provisioning will go through the school's own
  authorized workflow (a `SCHOOL_ADMIN` creating accounts, in a later
  phase), not public self-registration.

**Next up: Phase 5 — School Management** (school profile, logo upload,
branding, academic sessions, terms, classes, subjects — all properly
tenant-scoped using the `scope_to_school`/`ensure_same_school` pattern
established here).
