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
