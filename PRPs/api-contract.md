# TestPilot API Contract (Phase 2)

Single source of truth for backend and frontend agents building modules in parallel.
Field names are **snake_case**, ids are **integers**, timestamps ISO-8601 strings. Allowed enum values are in `PRPs/testpilot-prp.md` (DATABASE MODELS) and the enum classes in `backend/app/models/`.

## Conventions
- All `/api/*` routes require `Authorization: Bearer <access_token>`; resolve the user with `CurrentUser` / `DbSession` from `app.dependencies`.
- **Data isolation:** every query filters by `user_id == current_user.id`. A record owned by someone else returns **404**, never 403. When a body references another record (`project_id`, `requirement_id`, `test_case_id`) verify it belongs to the user (and the same project where applicable) else **404/422**.
- List endpoints return a **plain JSON array** (no envelope), accept `limit` (default 200, max 500) and `offset`, and a `q` text filter where listed. Sort newest first (`id` desc) unless stated.
- Create → **201** with the object. Update (PUT) takes the full editable field set, returns the object. Delete → **204**.
- Errors use `{"error": {"code": str, "message": str}}` (see `app/exceptions.py`); validation errors are FastAPI default 422.
- Models already exist; **do not change models or migrations**. If a change is truly needed, say so in your report.
- Pydantic v2 schemas validate enum fields with the model enum classes.

## Auth (`/auth/*`, no /api prefix)
| Endpoint | Body | Response |
|---|---|---|
| POST /auth/register | `{email, password (min 8), full_name}` | 201 `User` |
| POST /auth/login | JSON `{email, password}` | 200 `{access_token, token_type:"bearer"}` + `Set-Cookie: tp_refresh` (refresh token is never in a JSON body) |
| POST /auth/refresh | no body; cookie `tp_refresh`; header `X-Requested-With: TestPilot` | 200 `{access_token, token_type}` + rotated `tp_refresh`. Missing/invalid/expired/revoked cookie -> 401 and cookie cleared. Replay of a rotated token revokes the whole token family (401, cookie cleared) |
| POST /auth/logout | no body; cookie `tp_refresh`; header `X-Requested-With: TestPilot` | 204 always (idempotent); revokes the token and clears the cookie |
| GET /auth/me | - | `User` |
| PUT /auth/me | `{full_name}` | `User` |
| GET /auth/google | - | 302 to Google (501 error JSON if GOOGLE_CLIENT_ID unset) |
| GET /auth/google/callback | `code`,`state` | 302 to `{FRONTEND_URL}/auth/callback` with NO tokens in the URL (no query, no fragment), `Set-Cookie: tp_refresh`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store`. The frontend then calls `POST /auth/refresh` to get its access token |

**Refresh cookie `tp_refresh`:** `HttpOnly`, `SameSite=COOKIE_SAMESITE` (default `strict`), `Secure=COOKIE_SECURE` (default true when `FRONTEND_URL` is https), `Path=/auth`, `Max-Age=REFRESH_TOKEN_EXPIRE_DAYS*86400`, optional `Domain=COOKIE_DOMAIN` (default none). The access token is kept in memory by the frontend (never localStorage).

**CSRF on cookie endpoints (`/auth/refresh`, `/auth/logout`):** if an `Origin` header is present it must be in `CORS_ORIGINS`, else 403 `{"error":{"code":"FORBIDDEN",...}}`; and `X-Requested-With: TestPilot` is required, else 403. Frontend fetches must use `credentials: "include"`.

**CORS:** explicit origin allowlist (`CORS_ORIGINS`, `*` rejected), `allow_credentials=true`, headers `Authorization, Content-Type, X-Requested-With`, methods `GET, POST, PUT, DELETE, OPTIONS`.

`User` = `{id, email, full_name, is_active, is_verified, oauth_provider, created_at}` (never the hash).
`app/auth/jwt.py` and `get_current_user` in `app/dependencies.py` already exist - use them.

## Projects (`/api/projects`)
Fields: `{id, name, key, description, status, owner?: string, created_at, updated_at}`; `key` uppercased, unique per user (409 on conflict). Extra on GET one: `counts: {requirements, test_cases, test_runs, defects}`. Filters: `q`, `status`. DELETE cascades.

## Requirements (`/api/requirements`)
`{id, project_id, title, description, priority, status, test_case_count, created_at, updated_at}`. Filters: `project_id, priority, status, q`. GET one adds `test_cases: [{id,title,status}]`.

## Test cases (`/api/testcases`)
`{id, project_id, requirement_id|null, title, module, type, priority, status, preconditions, steps, expected_result, created_at, updated_at}` (`steps` is one string, newline-separated). Filters: `project_id, requirement_id, type, priority, status, q`. `GET /api/testcases/export` → `text/csv` of the filtered list (declare before `/{id}`).

## Test runs (`/api/testruns`)
List/one item: `{id, project_id, name, assignee, status, total_cases, executed, passed, created_at, updated_at}` where scope = project's test cases with status != Deprecated. Filters: `project_id, status, q`.
`GET /api/testruns/{id}` adds `cases: [{id, title, priority, steps, expected_result, result: {status, comment, executed_at} | null}]`.
`PUT /api/testruns/{id}/results/{case_id}` body `{status, comment}` (upsert; case must be in run scope) → the updated run (same shape as GET one). Run `status` is derived: no results → Planned, all executed → Completed, else In Progress.
`DELETE /api/testruns/{id}/results` → 204, clears results (status → Planned).

## Defects (`/api/defects`)
`{id, project_id, test_case_id|null, title, description, severity, status, assignee, created_at, updated_at}`. Filters: `project_id, severity, status, q`.

## Dashboard / reports
`GET /api/dashboard/summary?project_id=` →
```
{ test_cases:int, test_runs:int, executed:int, pass_rate:int(0-100), open_defects:int,
  results:{Passed:int,Failed:int,Blocked:int,Skipped:int},
  defects_by_severity:{Minor:int,Major:int,Critical:int,Blocker:int},
  runs:[{id,name,progress_pct:int}], recent_defects:[Defect x5] }
```
Open = status in (Open, In Progress). `pass_rate` = Passed / executed results.
`GET /api/reports/projects?project_id=&format=json|csv` →
`[{project_id, project, test_cases, requirements, coverage_pct, runs, executed, pass_rate, open_defects, defects}]` (coverage = requirements with >=1 test case / requirements).

## Frontend conventions
- Use existing `src/services/api.ts` (Axios; baseURL = VITE_API_URL, no prefix), `src/components/ui/*`, Tailwind, Framer Motion. No `any`, no `console.log`, no inline styles.
- One service file per module: `src/services/<module>Service.ts`. Do **not** edit `src/types/index.ts`; if you need extra response types define them in your service file.
- Replace the placeholder page components **in place** (same filenames/exports) so `App.tsx` routes keep working. Scoped lists read the current project from `useProject()` and pass `project_id`.
- Statuses/priorities render with `Badge`/`StatusBadge`. Forms use `FormField`; show API validation errors.
- Display ids are derived on the client: `TC-{id}`, `REQ-{id}`, `RUN-{id}`, `BUG-{id}`.
