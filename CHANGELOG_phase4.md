# Phase 4 — Multi-Tenancy & Tenant Isolation — CHANGELOG

Builds directly on the existing Phase 1–3 codebase. No models were
duplicated or replaced; no existing authentication code was rewritten.

## Files added

**Backend**
- `backend/app/core/tenancy.py` — the tenant-scoping toolkit:
  `require_school_user()`, `get_current_school()`, `require_school_role(...)`,
  `ensure_same_school(...)`, `scope_to_school(...)`.
- `backend/app/api/schools.py` — `GET /api/schools/me`,
  `GET /api/schools/{school_id}`.
- `backend/tests/test_tenancy_unit.py` — unit tests for
  `ensure_same_school` and `scope_to_school`.
- `backend/tests/test_tenant_isolation_api.py` — end-to-end cross-tenant
  tests (two schools, per-role users, `SUPER_ADMIN`).

**Docs**
- `CHANGELOG_phase4.md` (this file)
- Phase 4 section added to `README.md`

## Files modified

- `backend/app/main.py` — added `app.include_router(schools_router)`.
  `/api/health` and the existing auth routes are untouched.
- `frontend/src/types/school.ts` — new file, `School` type (not a
  modification, listed here for completeness).
- `frontend/src/api/schools.ts` — new file, `fetchMySchool()`.
- `frontend/src/pages/DashboardPage.tsx` — now fetches and displays the
  caller's school name for school-bound users (via `GET /api/schools/me`);
  `SUPER_ADMIN` users see "Platform administrator" instead, since they
  have no single home school.

No existing Phase 1–3 files were rewritten beyond the one-line router
registration in `main.py`.

## Database changes

**No Phase 4 database migration required.** Verified by running
`alembic revision --autogenerate` after all Phase 4 code was in place:
the generated migration's `upgrade()`/`downgrade()` were both empty
(`pass`), confirming zero schema drift, then discarded (not part of this
deliverable). Migration history unchanged:

```text
f98225df0d46 — Phase 2 core domain tables
4dc4f1df9355 — Phase 3 refresh tokens table
```

## New endpoints

| Method | Path | Behavior |
|---|---|---|
| GET | `/api/schools/me` | Returns the caller's own school. `403` for `SUPER_ADMIN` (no home school). |
| GET | `/api/schools/{school_id}` | Own school → `200`. `SUPER_ADMIN` → any school → `200`. Any other school's ID → `404`. |

## Security decisions

- **Tenant identity source of truth:** the authenticated `User` row
  loaded fresh from the DB by Phase 3's `get_current_user()`
  (`current_user.school_id`) — never a client-supplied ID, never the
  JWT's own claims.
- **404, not 403, for cross-tenant access by ID** — a wrong-tenant ID and
  a nonexistent ID return identical responses (status code and body),
  verified explicitly in
  `test_nonexistent_school_id_and_wrong_tenant_school_id_look_identical`.
- **`SUPER_ADMIN` is never implicitly "in" every school** —
  `get_current_school`/`require_school_user` both explicitly reject
  `SUPER_ADMIN`; cross-school access only happens in code that checks for
  the role explicitly (`get_school_by_id`).
- **Mass-assignment audit:** confirmed every existing Phase 2 `*Create`
  schema already excludes `school_id` — nothing to change there, but
  documented as the pattern to keep following.
- **Request-body/query-param `school_id` tampering has no effect** —
  `/api/schools/me` ignores any such value entirely (test:
  `test_changing_school_id_in_request_body_does_not_bypass_isolation`).

## Tenant-isolation strategy (for future phases to reuse)

For any new school-owned resource:
- **Single-resource read/update/delete:** fetch by ID, then call
  `ensure_same_school(current_user, resource.school_id)` before using it.
- **List/search:** wrap the base query with
  `scope_to_school(query, Model, current_user)`.
- **Create:** derive `school_id` from `current_user.school_id`
  server-side (via `get_current_school()`/`require_school_user()`); never
  accept it from the request body for `SCHOOL_ADMIN`/`TEACHER`/`STUDENT`.
- Where a resource has no `school_id` column of its own (e.g. a future
  `Score` scoped through its `Student`), join to the owning table and
  filter there instead of adding a redundant column.

## Tests added

- `test_tenancy_unit.py` — 5 tests (ensure_same_school ×3,
  scope_to_school ×2).
- `test_tenant_isolation_api.py` — 12 tests: own-school access (School A,
  School B), own-school access by ID, cross-school access blocked by URL
  ID (both directions), identical 404 for wrong-tenant vs. nonexistent
  ID, `SUPER_ADMIN` cross-school access, `SUPER_ADMIN` 404 for a
  nonexistent school, `SUPER_ADMIN` 403 on `/me`, request-body `school_id`
  tampering ignored, unauthenticated request rejected, inactive user
  rejected.

## Final test results

```
45 passed
```

- 28 pre-existing tests (Phase 1 health check, 6 Phase 2 model tests, 14
  Phase 3 auth tests) — all still pass, unmodified.
- 17 new Phase 4 tests — all pass.

## Frontend build result

```
npm run build
✓ 142 modules transformed
✓ built in 2.83s
```

Clean build, no TypeScript errors, no warnings.

## Files added (round 2 — UX follow-up from live Phase 3 testing)

- `frontend/src/utils/roleLabels.ts` — maps raw role enum values to
  human-readable labels.
- `frontend/src/pages/RegisterSchoolComingSoonPage.tsx` — static
  placeholder for the future Phase 5 "Create your school account" flow.
  Collects no input, makes no API calls, writes nothing to the database.

## Files modified (round 2)

- `frontend/src/pages/LoginPage.tsx` — added product name + tagline
  above the form, and a "New school? Create your school account" link to
  the new placeholder page. Login logic itself (email + password only, no
  role/school selection) is unchanged.
- `frontend/src/pages/DashboardPage.tsx` — now uses `roleLabel()` for a
  human-readable role, and shows a "Global Administration" badge (never
  a fabricated school) for `SUPER_ADMIN`.
- `frontend/src/App.tsx` — added the `/register-school` route.
- `frontend/tsconfig.json` — added `"ignoreDeprecations": "5.0"`. Not a
  Phase 4 feature — a fresh `npm install` picked up TypeScript 5.9.3
  (satisfies the existing `^5.6.2` range), which now warns that
  `baseUrl` is deprecated; this silences that specific warning so
  `npm run build` keeps succeeding. No other build config changed.
- `README.md` — added "Login and identity UX" and "Future Phase 5
  registration architecture" subsections under Phase 4.

## UX improvements (this round)

- Login page clearly identifies the product ("School Results Management
  — Manage assessments, results and reports").
- Dashboard shows school-bound users their school name, email, and a
  human-readable role (not a raw enum value).
- `SUPER_ADMIN` sees an explicit "Global Administration" identity instead
  of any (fabricated) school context.
- A placeholder link for future school registration exists and is
  honest about not being available yet — no incomplete/fake records are
  created from it.

## Verification re-run after this round

- Backend: `45 passed` (unchanged — no backend files touched this round).
- Frontend: `npm run build` — clean, 144 modules, no errors.
- Live smoke test (via `TestClient`, not just pytest): created a school +
  a `SCHOOL_ADMIN` + a `SUPER_ADMIN`, logged in as both, confirmed
  `SCHOOL_ADMIN` → `/api/schools/me` returns their school (200),
  `SUPER_ADMIN` → `/api/schools/me` → 403, `SUPER_ADMIN` →
  `/api/schools/{id}` → 200. Matches the documented behavior exactly.
- Migration history unchanged and re-verified:
  `f98225df0d46` → `4dc4f1df9355`.
- `/api/health` still returns `{"status": "ok", "environment":
  "development"}`.

## Known limitations intentionally deferred to Phase 5+

- Full school-management CRUD (edit profile, logo upload, branding) —
  Phase 5.
- No teacher/student/class/subject/assessment/score/result endpoints
  exist yet, so `scope_to_school`/`ensure_same_school` aren't exercised
  against those resources yet — only against `School` itself. The pattern
  is established and tested; applying it to each new resource is each
  later phase's job as that resource's endpoints get built.
- No audit logging of cross-tenant access attempts yet (Phase 2's
  `AuditLog` model exists; wiring it up is a later phase).
- Rate limiting / brute-force protection on auth endpoints — not in scope
  for Phase 3 or 4.
