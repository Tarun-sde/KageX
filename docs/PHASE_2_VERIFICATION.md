# Phase 2 Verification — 2026-10-04

## 1. PHASE 2 STATUS

**INCOMPLETE — hosted CI verification pending.** Local implementation and acceptance checks pass. Phase 3 has not started.

## 2. BASELINE VERIFIED

Preserved the Phase 1 foundation and valid partial Phase 2 work. All nine original backend tests pass; foundation frontend checks remain covered with the workspace now requiring authentication. Read engineering/state/roadmap/decisions/design documents; inspected repository structure, Git status/diff, existing migrations/auth/ownership/storage/frontend/Docker/CI before continuing. The project owner confirmed Phase 1 hosted CI passed.

## 3. FILES CREATED

Paths delivered relative to repository root, including the preserved partial Phase 2 files:

- Backend: `backend/app/api/{auth,projects}.py`, `backend/app/core/{security,body_limit}.py`, `backend/app/models/__init__.py`, `backend/app/schemas/__init__.py`.
- Frontend: `frontend/src/app/{AuthProvider.tsx,auth-context.ts}`, `frontend/src/components/ProtectedRoute.tsx`, `frontend/src/pages/{AuthPage,ProjectPage}.tsx`, `frontend/src/services/{auth,projects}.ts`.
- Database: `backend/alembic/versions/6e605e1f5bed_identity_sessions_and_owned_projects.py`.
- Ingestion/storage: `backend/app/services/{storage,github,ingestion}.py`.
- Infrastructure: no new deployment files; existing Docker/CI configuration extended. Browser configuration: `frontend/playwright.config.ts`.
- Tests: `backend/tests/{__init__,conftest,test_identity_projects,test_ingestion}.py`, `frontend/e2e/projects.spec.ts`.
- Documentation: this verification record.

## 4. FILES MODIFIED

- Backend settings/main/errors/session metadata/Alembic environment: configure sessions/storage/limits, register routes, safe errors, support real migration tests. Dockerfile creates private storage. pyproject/uv.lock add Argon2, email validation and runtime HTTP client.
- Frontend App/Workspace/API client/styles: protected account/project flows using existing visual primitives. Vitest tests expanded. package/lock/TypeScript/Vite/lint/format settings include Playwright and exclude generated test output.
- `.env.example`, `.gitignore`, `docker-compose.yml`, `.github/workflows/ci.yml`: limits, ignored private storage, persistent non-root volume, PostgreSQL/migration/E2E verification.
- `README.md`, `AGENT.md`, `docs/PROJECT_STATE.md`, `docs/TECHNICAL_DECISIONS.md`: actual API, setup, storage/auth choices, commands, limitations, evidence and pending hosted gate. Frozen roadmap/design/ML methodology unchanged.

## 5. DATABASE SCHEMA

`users`: UUID, unique normalized email, Argon2 hash, active flag, timestamps. `auth_sessions`: hashed-token primary key, user FK (cascade deletion), expiry/index, timestamps. `projects`: UUID, indexed owner FK (restrict user deletion), name, constrained source/status enums, optional canonical GitHub URL/error code, nonnegative file/byte counts, timestamps. No other domain tables added.

## 6. AUTHENTICATION

First-party PostgreSQL-backed opaque sessions; 256-bit random tokens, SHA-256 digests persisted, one-hour default absolute expiry. Argon2id passwords, 12–128 characters, salts and rehash support. Login rotates current session, logout revokes it; expired/inactive sessions reject requests. Cookies are HttpOnly/SameSite=Lax; production adds Secure/host-only `__Host-` prefix and requires HTTPS origins. Unsafe requests require trusted Origin plus custom header. No browser credential storage/JWT/signing key.

## 7. PROJECT OWNERSHIP

Central dependency queries both project UUID and authenticated user UUID for every read/mutation/ZIP/GitHub request. Foreign and nonexistent resources both return 404; owner fields are not accepted in writes. Mutations lock the row with NOWAIT; collisions return 409 PROJECT_BUSY. Read lists are owner-filtered and bounded to 50 rows.

## 8. PROJECT API

Under `/api/v1`: POST/GET `/projects`; GET/PATCH/DELETE `/projects/{id}`; GET `/projects/source-limits`; POST `/projects/{id}/source/zip` (raw bytes); POST `/projects/{id}/source/github` (URL JSON). PATCH only renames. READY source is immutable. Auth routes: POST register/login/logout and GET me under `/auth`. See README for request/response/status details.

## 9. SECURE INGESTION

ZIP/public GitHub share one extractor. Defaults: 25 MiB compressed, 100 MiB expanded, 10 MiB/file, 2000 entries, ratio 100, 30-second deadline. JSON request bodies limited to 16 KiB. Central-directory preflight bounds allocation and rejects ambiguous offsets. Reject traversal, absolute/control/backslash paths, links/special files, conflicts, encrypted/unsupported ZIPs, bad CRC, excessive resources. Nested archives/binaries remain inert. No execution, imports, shell commands, builds or repository installs. Private UUID storage, context-managed staging, normal failure cleanup and persisted FAILED; retry creates fresh staging. Deletion quarantines/restores on rollback, then purges after commit. Crash limitations are explicit below.

## 10. GITHUB INGESTION

**IMPLEMENTED**: public default-branch repositories at `https://github.com/owner/repository`, with optional `.git`/trailing slash. No private tokens, branch URLs, credentials, queries, fragments, ports or arbitrary hosts/protocols. Fixed HTTPS codeload download, redirects/proxy environment disabled, five-second network operation timeout plus total deadline/size checks. Live octocat/Hello-World import reached READY with one file/13 bytes; verification project/source removed.

## 11. CELERY / BACKGROUND TASKS

Phase 2 ingestion is synchronous and bounded; no ingestion queue/task or fake job status exists. UI shows preparation activity; persisted states are CREATED, READY, FAILED. Real Celery broker/worker/result transport still returns pong. Future long-running analysis retains the frozen asynchronous architecture.

## 12. FRONTEND

Sign in/register, session restoration, protected routing, owner project list/create/detail, ZIP/public GitHub input, busy/error/empty/retry states, rename/delete, logout and expiry redirect. READY explicitly means source prepared; no fake analysis or predictions. Desktop/mobile browser flows passed with no page errors/overflow.

## 13. SECURITY VERIFICATION

PASS: Argon2id-only password persistence and safe responses/logs; protected session routes; all-route IDOR denial; traversal, bombs, symlink/special-file rejection; inert-source marker unchanged; fixed-host URL restrictions; no probable secret patterns in tracked/unignored files. `.env` and local source remain ignored. This scoped audit is not a claim of production penetration testing.

## 14. TEST RESULTS

Backend **77 passed** (31 Python files type-checked); frontend **14 passed**; Playwright **2 passed** at 1440px/390px. No failed tests in the final runs. Temporary failure reports were resolved, not excluded. Locked uv/npm installation succeeded; npm reported zero dependency vulnerabilities.

## 15. SECURITY TEST RESULTS

Covered password hashes, duplicate/normalized emails, invalid credentials, safe validation/logging, expired/inactive/forged/revoked/rotated sessions, production cookies, CSRF/CORS, oversized JSON, ownership for CRUD and both ingestion routes, forged ownership/status fields, concurrent locks, ZIP traversal/control/absolute/NUL paths, symlinks/FIFO/devices/sockets, path conflicts, malformed/empty/encrypted/unsupported/CRC archives, compressed/expanded/per-file/count/ratio limits, forged central counts/offsets, deadlines, disconnects, upload/storage failure cleanup, retry, storage symlink escape, delete rollback, isolated sources, nested inert ZIP/binaries, SSRF URL variants, download redirects/size/timeouts, shared GitHub extraction.

## 16. STATIC CHECK RESULTS

PASS: Ruff, Ruff format check (31 files), strict mypy (31 files), ESLint, Prettier, TypeScript, Vite production build, `git diff --check`. GNU Make absent; commands ran directly using the installed uv binary. See README for equivalent reproducible commands.

## 17. DATABASE MIGRATION RESULTS

PASS: migration-generated duplicate enum checks corrected; real isolated PostgreSQL schemas upgraded for integration tests. Round-trip test checks schema, downgrades to baseline/base and re-upgrades. Additionally a fresh disposable PostgreSQL database in Docker passed upgrade → check → downgrade to base → re-upgrade → check, then was removed. Existing application database remains at head; container `alembic check` reports no new operations.

## 18. DOCKER STATUS

PASS: Compose config; rebuilt current images; migrations exited 0; backend/frontend/PostgreSQL/Redis/Celery healthy. Runtime readiness and actual queued ping passed. Browser account/project/ZIP flows and public GitHub import ran against containers. Non-root source root mode 0700 verified. Final staging/trash entry counts both zero. Native API readiness at 8011 and Vite response at 5174 also verified, then temporary native processes stopped. Compose remains running at 5173/8000.

## 19. CI STATUS

Updated workflow runs backend checks against PostgreSQL (including migrations/security tests), frontend checks/build, Docker runtime gates and Playwright. PASS: local commands, YAML parsing and job/step structure; manually reviewed service/command wiring. **Hosted Phase 2 GitHub Actions: NOT TESTED.** No push/commit or successful hosted run for these changes; formal phase completion remains blocked on that gate.

## 20. PHASE 0 / PHASE 1 REGRESSION CHECK

PASS: frozen per-language strategy, Java class/Python function/JavaScript file granularities, TypeScript MODEL_UNAVAILABLE, no-source-execution rule, dependency health, worker transport, startup, routing and core tests remain intact. No analyzer or ML was added. Phase 0 documents/design/roadmap were not rewritten.

## 21. PHASE 2 ACCEPTANCE CRITERIA

Every requested criterion is listed below; N/A only applies to the conditional asynchronous ingestion task. Hosted CI is the sole unverified gate.

| Area | Criterion | Result |
|---|---|---|
| Authentication | User registration works | PASS |
| Authentication | Secure password hashing works | PASS |
| Authentication | Login works | PASS |
| Authentication | Current-user endpoint works | PASS |
| Authentication | Protected routes reject unauthenticated users | PASS |
| Authentication | Logout/session invalidation works where applicable | PASS |
| Authentication | No plaintext passwords stored | PASS |
| Authentication | Sensitive auth data is not returned/logged | PASS |
| Database | User migration exists | PASS |
| Database | Project migration exists | PASS |
| Database | Ownership foreign key exists | PASS |
| Database | migrations apply from clean database | PASS |
| Database | relevant constraints/indexes exist | PASS |
| Authorization | Projects belong to users | PASS |
| Authorization | User can access own project | PASS |
| Authorization | User cannot access another user's project | PASS |
| Authorization | User cannot modify another user's project | PASS |
| Authorization | User cannot delete another user's project | PASS |
| Project API | Project create works | PASS |
| Project API | Project list is owner-scoped | PASS |
| Project API | Project detail is owner-scoped | PASS |
| Project API | Project update is owner-scoped | PASS |
| Project API | Project delete is owner-scoped | PASS |
| Upload Security | Upload limit exists | PASS |
| Upload Security | archive validation exists | PASS |
| Upload Security | ZIP traversal prevented | PASS |
| Upload Security | extracted-size limit exists | PASS |
| Upload Security | file-count limit exists | PASS |
| Upload Security | symlink policy exists | PASS |
| Upload Security | failed uploads clean temporary data | PASS |
| Upload Security | project storage isolated | PASS |
| GitHub Intake | GitHub URL validation | PASS |
| GitHub Intake | GitHub.com host restriction | PASS |
| GitHub Intake | no arbitrary URL fetching | PASS |
| GitHub Intake | public-repository limitation documented if applicable | PASS |
| GitHub Intake | no repository code execution | PASS |
| Background Jobs | ingestion job can run if asynchronous | N/A — synchronous ingestion |
| Background Jobs | project state updates correctly | PASS |
| Background Jobs | failures result in safe FAILED state | PASS |
| Background Jobs | retries do not corrupt storage | PASS |
| Frontend | Login UI works | PASS |
| Frontend | Registration UI works | PASS |
| Frontend | Auth state works | PASS |
| Frontend | Protected project area works | PASS |
| Frontend | Project list works | PASS |
| Frontend | Project creation works | PASS |
| Frontend | Upload/source input works where implemented | PASS |
| Frontend | error/loading states exist | PASS |
| Frontend | no fake analysis data exists | PASS |
| Quality | backend lint passes | PASS |
| Quality | backend format check passes | PASS |
| Quality | backend type check passes | PASS |
| Quality | backend tests pass | PASS |
| Quality | frontend lint passes | PASS |
| Quality | frontend format passes | PASS |
| Quality | frontend type check passes | PASS |
| Quality | frontend tests pass | PASS |
| Quality | frontend production build passes | PASS |
| Infrastructure | Docker configuration still valid | PASS |
| Infrastructure | PostgreSQL works | PASS |
| Infrastructure | Redis works | PASS |
| Infrastructure | Celery works | PASS |
| Infrastructure | migrations work in containers | PASS |
| CI | GitHub Actions configuration updated as necessary | PASS |
| CI | hosted CI run is green | NOT TESTED |
| Security | no user source execution | PASS |
| Security | no fake ML output | PASS |
| Security | no secrets committed | PASS |
| Security | no cross-user project access | PASS |
| Security | archive traversal tests pass | PASS |

## 22. KNOWN LIMITATIONS

- Local development scope: no authentication throttling, user/global storage quotas, automatic retention/garbage collection or crash reconciliation. Bounded per-request resources are implemented; these deployment concerns are explicit in TD-011.
- Filesystem/DB operations cannot be crash-atomic. Abrupt death can leave staging/orphan source/quarantine; offline operator reconciliation is documented. Normal request failure cleanup and rollback are tested.
- Same-site cookie deployment required. No account reset/verification/OAuth; sessions expire absolutely and require login again. Expired session rows are pruned on subsequent login for that user.
- Strict ZIP policy rejects linked/ZIP64/split/self-extracting/unsupported-compression repositories. GitHub imports follow default-branch HEAD and do not store a resolved commit SHA. Nested archives and binaries are retained without inspection.
- Synchronous preparation holds a project row/connection; configured resource limits keep Phase 2 bounded. Network deadlines are cooperative and an active read may extend by up to its five-second timeout.
- E2E creates disposable accounts in the dev database; test projects are deleted. Hosted CI still pending.

## 23. PHASE 3 READINESS

**NOT READY** until hosted Phase 2 CI is green. No Phase 3 work was started.

## 24. IMPORTANT NOTES FOR PHASE 3

Preserve central ownership checks, session/CSRF protections, bounded shared ingestion and source isolation. READY means only source prepared. Add analysis-run persistence/workspaces/Celery lifecycle when authorized, with retention/crash recovery decisions explicit. Do not execute submitted code or install repository dependencies. Preserve per-language schemas/models and TypeScript MODEL_UNAVAILABLE; no prediction without a compatible validated model.
