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

**Next up: Phase 2 — Database** (SQLAlchemy models, relationships,
constraints, Alembic migrations, seed data).
