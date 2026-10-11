# PRP: TestPilot

> Implementation blueprint for parallel agent execution

---

## METADATA

| Field | Value |
|-------|-------|
| **Product** | TestPilot |
| **Type** | SaaS |
| **Version** | 1.0 |
| **Created** | 2026-10-10 |
| **Complexity** | Medium |

---

## PRODUCT OVERVIEW

**Description:** Test case management tool for QA engineers and small teams to save, organise and execute test cases, track runs and log defects.

**Value Proposition:** Replaces spreadsheets with a structured, searchable test repository that links requirements → test cases → runs → defects, with pass-rate and coverage reporting.

**MVP Scope:**
- [ ] User registration/login (JWT) and Google OAuth
- [ ] Projects, requirements and test case CRUD (save/search/filter test cases)
- [ ] Test runs with per-case execution (Passed / Failed / Blocked / Skipped + comment)
- [ ] Defect tracking, with one-click "log defect" from a failed result
- [ ] Dashboard + project reports (pass rate, requirement coverage, defects by severity), CSV export

**Assumptions** (INITIAL.md left these open; override if wrong):
- UI library: **Tailwind CSS** (+ Framer Motion), not Chakra
- Payments: **None** for MVP
- Data is private per user (every row has `user_id`); team sharing/roles are out of scope for v1
- Reference UI prototype: `../testpilot/` (static HTML/JS) — mirror its entities, fields and screens

---

## TECH STACK

| Layer | Technology | Skill Reference |
|-------|------------|-----------------|
| Backend | FastAPI + Python 3.11+ | skills/BACKEND.md |
| Frontend | React + TypeScript + Vite | skills/FRONTEND.md |
| Database | PostgreSQL + SQLAlchemy + Alembic | skills/DATABASE.md |
| Auth | JWT + bcrypt + Google OAuth | skills/BACKEND.md |
| UI | Tailwind CSS + Framer Motion | skills/FRONTEND.md |
| Testing | pytest + React Testing Library | skills/TESTING.md |
| Deployment | Docker + GitHub Actions | skills/DEPLOYMENT.md |

---

## DATABASE MODELS

All models: `id` (PK), `created_at`, `updated_at`. All non-User models: `user_id` (FK → users, indexed, ON DELETE CASCADE).

### User
- email (unique), hashed_password (nullable for OAuth), full_name, is_active, is_verified, oauth_provider

### RefreshToken
- user_id (FK), token_hash, expires_at, revoked

### Project
- name, key (unique per user, upper-case), description, status (`Active|On Hold|Archived`)
- Relationships: has many Requirement, TestCase, TestRun, Defect (cascade delete)

### Requirement
- project_id (FK), title, description, priority (`Low|Medium|High|Critical`), status (`Proposed|Approved|Implemented|Verified`)

### TestCase
- project_id (FK), requirement_id (FK, nullable), title, module, type (`Functional|Regression|Smoke|API|UI|Performance|Security`), priority, status (`Draft|Ready|Deprecated`), preconditions, steps (text, one per line), expected_result
- Display id per project: `TC-###` (derived, not stored)

### TestRun
- project_id (FK), name, assignee (text or nullable FK → users), status (`Planned|In Progress|Completed`; derived from results)

### TestResult
- test_run_id (FK), test_case_id (FK), status (`Passed|Failed|Blocked|Skipped`), comment, executed_at
- Unique (test_run_id, test_case_id)

### Defect
- project_id (FK), test_case_id (FK, nullable), title, description, severity (`Minor|Major|Critical|Blocker`), status (`Open|In Progress|Resolved|Closed`), assignee

---

## MODULES

### Module 1: Authentication
**Agents:** DATABASE-AGENT + BACKEND-AGENT + FRONTEND-AGENT

**Backend Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Create account |
| POST | /auth/login | Get access + refresh tokens |
| POST | /auth/refresh | Rotate refresh token |
| GET | /auth/me | Current user |
| GET | /auth/google | Google OAuth flow (+ callback) |

**Frontend Pages:**
| Route | Page | Components |
|-------|------|------------|
| /login | LoginPage | LoginForm, GoogleButton |
| /register | RegisterPage | RegisterForm |
| /profile | ProfilePage | ProfileForm |

---

### Module 2: Projects
**Agents:** BACKEND-AGENT + FRONTEND-AGENT

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/projects | List (search, status filter) |
| POST | /api/projects | Create |
| GET | /api/projects/{id} | Get one + counts |
| PUT | /api/projects/{id} | Update |
| DELETE | /api/projects/{id} | Delete (cascades) |

| Route | Page | Components |
|-------|------|------------|
| /projects | ProjectListPage | DataTable, StatusBadge |
| /projects/new, /projects/:id/edit | ProjectFormPage | ProjectForm |
| /projects/:id | ProjectDetailPage | StatsCards, tabs to child resources |

---

### Module 3: Requirements
**Agents:** BACKEND-AGENT + FRONTEND-AGENT

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/requirements | List (`project_id`, priority, status, `q`) |
| POST | /api/requirements | Create |
| GET | /api/requirements/{id} | Get one + linked test cases |
| PUT | /api/requirements/{id} | Update |
| DELETE | /api/requirements/{id} | Delete (test cases keep, FK set null) |

| Route | Page | Components |
|-------|------|------------|
| /requirements | RequirementListPage | DataTable, FilterBar |
| /requirements/new, /requirements/:id/edit | RequirementFormPage | RequirementForm |
| /requirements/:id | RequirementDetailPage | LinkedCasesList |

---

### Module 4: Test Cases (core)
**Agents:** BACKEND-AGENT + FRONTEND-AGENT

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/testcases | List (`project_id`, type, priority, status, `q`, pagination) |
| POST | /api/testcases | Create |
| GET | /api/testcases/{id} | Get one |
| PUT | /api/testcases/{id} | Update |
| DELETE | /api/testcases/{id} | Delete |
| GET | /api/testcases/export | CSV export of filtered list |

| Route | Page | Components |
|-------|------|------------|
| /testcases | TestCaseListPage | DataTable, FilterBar, CsvButton |
| /testcases/new, /testcases/:id/edit | TestCaseFormPage | TestCaseForm (steps editor) |
| /testcases/:id | TestCaseDetailPage | StepsList, ResultHistory, LinkedDefects |

---

### Module 5: Test Runs & Execution
**Agents:** BACKEND-AGENT + FRONTEND-AGENT

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/testruns | List with progress |
| POST | /api/testruns | Create |
| GET | /api/testruns/{id} | Get run + cases + results |
| PUT | /api/testruns/{id} | Update |
| DELETE | /api/testruns/{id} | Delete |
| PUT | /api/testruns/{id}/results/{case_id} | Set result + comment; recompute run status |
| DELETE | /api/testruns/{id}/results | Reset all results |

Run scope = non-deprecated test cases of the run's project.

| Route | Page | Components |
|-------|------|------------|
| /testruns | TestRunListPage | DataTable, ProgressBar |
| /testruns/new, /testruns/:id/edit | TestRunFormPage | TestRunForm |
| /testruns/:id | TestRunExecutionPage | ResultButtons, CommentInput, LogDefectButton, SummaryBar |

---

### Module 6: Defects
**Agents:** BACKEND-AGENT + FRONTEND-AGENT

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/defects | List (`project_id`, severity, status, `q`) |
| POST | /api/defects | Create (accepts prefill from failed result) |
| GET | /api/defects/{id} | Get one |
| PUT | /api/defects/{id} | Update |
| DELETE | /api/defects/{id} | Delete |

| Route | Page | Components |
|-------|------|------------|
| /defects | DefectListPage | DataTable, SeverityBadge |
| /defects/new, /defects/:id/edit | DefectFormPage | DefectForm |
| /defects/:id | DefectDetailPage | LinkedCase |

---

### Module 7: Dashboard, Reports & Settings
**Agents:** BACKEND-AGENT + FRONTEND-AGENT

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/dashboard/summary | KPIs, result counts, defects by severity, run progress (`project_id` optional) |
| GET | /api/reports/projects | Per-project cases, coverage %, pass rate, defects (JSON or `?format=csv`) |
| GET | /health | Liveness check |

| Route | Page | Components |
|-------|------|------------|
| /dashboard | DashboardPage | KpiCard, DoughnutChart, BarChart, RecentDefects |
| /reports | ReportsPage | SummaryTable, Charts, CsvButton |
| /settings | SettingsPage | ThemeToggle, ProjectSwitcher defaults |

Global **project switcher** in the app shell scopes lists and the dashboard (sent as `project_id`).

---

## COUNTS

| Item | Count |
|------|-------|
| Modules | 7 |
| Models | 8 |
| Endpoints | 36 |
| Pages | 26 |

---

## PHASE EXECUTION PLAN

**Phase 1: Foundation (4 agents in parallel)**
- DATABASE-AGENT: All models, Alembic initial migration, database.py
- BACKEND-AGENT: main.py, config.py, project structure, auth utilities, CORS, error format
- FRONTEND-AGENT: Vite + TS + Tailwind setup, router, app shell (sidebar/topbar), API client, base components
- DEVOPS-AGENT: Dockerfiles, docker-compose (api, web, postgres), CI/CD, `.env.example`

**Validation Gate 1:** `pip install -r requirements.txt`, `alembic upgrade head`, `npm install`, `docker-compose config`

**Phase 2: Modules (backend + frontend parallel per module)**
- Auth: JWT endpoints + Login/Register/Profile pages
- Projects, Requirements, Test Cases: API + list/form/detail pages
- Test Runs: API + execution page (depends on Test Cases, Projects)
- Defects: API + pages (depends on Test Cases)
- Dashboard/Reports: aggregate endpoints + charts (last, depends on all)

**Validation Gate 2:** `ruff check backend/`, `mypy backend/app`, `npm run lint`, `npm run type-check`

**Phase 3: Quality (3 agents in parallel)**
- TEST-AGENT: pytest (auth, ownership isolation, run status derivation, coverage calc) + RTL tests, 80%+ coverage
- REVIEW-AGENT: Security audit (per-user data isolation on every query, token handling, input validation), performance (N+1 on progress/coverage queries, indexes)
- RESEARCH-AGENT: Validate Google OAuth flow and refresh-token rotation best practices

**Final Validation:** Full test suite, docker build, health checks

---

## VALIDATION GATES

| Gate | Commands |
|------|----------|
| 1 | `alembic upgrade head`, `npm install`, `docker-compose config` |
| 2 | `ruff check backend/`, `npm run type-check` |
| 3 | `pytest --cov --cov-fail-under=80`, `npm test` |
| Final | `docker-compose up -d`, `curl localhost:8000/health` |

---

## ACCEPTANCE CRITERIA

- [ ] Users can register, log in (password and Google) and refresh sessions
- [ ] Users can CRUD their projects, requirements, test cases, runs and defects
- [ ] A user can never read or modify another user's data (tested)
- [ ] Executing a run updates its status and progress automatically
- [ ] A failed result can be turned into a prefilled defect
- [ ] Dashboard and reports match the underlying data; CSV exports work
- [ ] 80%+ test coverage; Docker builds and `/health` returns 200

---

## ENVIRONMENT VARIABLES

```env
DATABASE_URL=postgresql://user:password@localhost:5432/testpilot
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-secret
VITE_API_URL=http://localhost:8000
```

---

## NEXT STEP

Execute with parallel agents:
/execute-prp PRPs/testpilot-prp.md
