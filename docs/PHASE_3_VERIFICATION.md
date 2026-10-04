# Phase 3 verification — 2026-10-04

**INCOMPLETE — hosted CI verification pending**

Local implementation and acceptance checks pass. No hosted run for these Phase 3 changes has been observed. The owner's earlier green GitHub Actions confirmation closes Phase 2 only. Phase 4 is **NOT READY** and has not started. No commit, push or deployment was performed.

## Continuation audit

Resumed the existing dirty repository, preserving the prior Phase 2 closure documentation and valid Phase 3 work. Read AGENT.md, PROJECT_STATE.md, the Phase 3 roadmap, existing changes and implementation. The starting core already included the migration, four adapters, safe tool boundary, source discovery, analysis lifecycle, APIs and frontend panel. The starting lifecycle tests had a typing error in their archive helper; correcting its covariant input type allowed all 96 existing tests to pass.

Remaining work completed: stricter metric-schema validation; Python multiline-string/normalized MI handling; complete warning counts; Celery hard/soft deadlines; parent/process cleanup guards; exact Java runtime metadata; native/CI trusted-tool setup; Docker resource limits and CK artifact permissions; frontend polling/failure and real browser tests; upgrade/data-preservation tests; no-execution sentinels; documentation. Browser validation found and fixed the root-owned unreadable CK JAR. A browser selector was corrected to use the accessible combobox role. No completed feature was recreated.

## Actual verification results

| Check | Result |
|---|---|
| Backend `ruff check .` | PASS |
| Backend `ruff format --check .` | PASS — 50 Python files |
| Backend `mypy .` | PASS — 50 Python files |
| Backend `pytest -q` | PASS — **105 tests**: 77 baseline, 18 analyzer/security, 10 analysis lifecycle/API/migration |
| Final focused analyzer test rerun after shell-metacharacter sentinel | PASS — **18 tests** |
| Frontend `npm run lint` | PASS |
| Frontend `npm run format:check` | PASS |
| Frontend `npm run typecheck` | PASS |
| Frontend `npm test` | PASS — **18 tests** in two files |
| Frontend `npm run build` | PASS |
| Frontend `npm run test:e2e` | PASS — **4 tests** against running Docker at 1440px / 390px |
| `docker compose config --quiet` | PASS |
| Docker builds and startup | PASS — API, migration, worker and frontend images; five long-running services healthy |
| `/health`, `/ready` | PASS — PostgreSQL/Redis ready |
| Actual Redis/Celery ping | PASS — queued `pong` result |
| Actual Redis/Celery analysis | PASS — browser-created mixed ZIP reaches COMPLETED with **nine entities** from all four languages |
| Worker runtime | PASS — UID 10001, Python 3.14.8, Radon 6.0.1, Java 17.0.20.1, Node 24.14.0 |
| Worker source/scratch checks | PASS — source write rejected with EROFS, CK readable by worker, zero residual analysis workspaces after normal runs |
| Container `alembic check` | PASS — no pending operations |
| Fresh PostgreSQL database | PASS — upgrade → check → downgrade to base → re-upgrade → check; disposable database removed |
| Phase 2 data-preserving migration | PASS — existing user/session/READY project survives Phase 3 upgrade; analysis works; Phase 3 downgrade/re-upgrade removes only analysis data |
| CI YAML structure | PASS — parsed and checked expected backend/frontend/infrastructure jobs |
| `git diff --check` | PASS |
| Hosted Phase 3 GitHub Actions | **NOT TESTED — pending** |

GNU Make is absent locally; equivalent commands ran directly. The native Python runtime was 3.14.7, Java 25.0.4.1 and Node 22.23.1; exact runtime versions are persisted. Docker verification used the production-shaped worker toolchain above. Native compiled wrapper artifacts were copied from the trusted Docker build because the host has a JRE but no javac. These ignored artifacts are not committed. CI installs a JDK 17 and compiles only KageX's own wrapper.

The final Compose images were rebuilt and all five services are healthy. Successful browser projects were removed by their tests; four known fixture projects left by earlier failed browser attempts were subsequently removed through their owned APIs. Disposable test accounts remain, as in Phase 2. The real `.env` was not edited and remains ignored.

## Persistence and lifecycle

Migration `f2de3d2ac9dd` follows `6e605e1f5bed` and adds:

- `analysis_runs`: UUID, project FK with cascade, constrained QUEUED/RUNNING/COMPLETED/FAILED state, timezone-aware creation/start/completion/deadline, safe errors, JSONB summary/warnings. Project/time index and partial unique index on active project runs.
- `analysis_entities`: UUID and cascading run FK; language/granularity/path/name/line range; JSONB metrics and warnings; analyzer name/version and schema version. Unique run/language/path/name/start identity, valid-line-range check, run/language/id index.

Owner-scoped request → committed QUEUED → UUID-only Celery task → RUNNING → bounded discovery/parsers → atomic entity publication and COMPLETED. Failures persist FAILED; no partial entities escape. Completed results are immutable through application APIs. One active run is allowed per project. Duplicate task deliveries use a PostgreSQL advisory lock and terminal no-op; redelivery never extends the original deadline. Explicit user retry creates a new run. Project READY still means source prepared.

Queue publication failure persists a safe error. An API crash between commit/publication can leave QUEUED; stale run reads/new-run/delete expire it. Worker failure can be redelivered within its original deadline. There is no outbox, periodic sweeper or infinite automatic retry. Celery acknowledges late and rejects on worker loss; JSON serialization and prefetch one are enforced. Soft/hard limits are total analysis timeout +10/+20 seconds. PostgreSQL is authoritative, not Celery result state.

## Tool and security evidence

[METRIC_SCHEMAS.md](METRIC_SCHEMAS.md) lists every actual metric, semantic limitation, extension, version and limit. Java uses CK 0.7.0 class metrics, Python Radon 6.0.1/AST function metrics, JavaScript ESLint 10.12.0/ts-morph 28.0.0 file metrics, TypeScript ts-morph 28.0.0/TypeScript 6.0.2 file metrics. All schemas preserve their granularity; no fake prediction fields exist.

Tests verify Java package/nested identity and known WMC/NOC/DIT, Python complexity/LOC/parameters/nested methods/async/encoding/multiline strings, JS complexity/counts/imports/ignored malicious ESLint config and inline rules, TS/TSX and MTS/CTS parsing without dependencies, and malformed input for all languages. Side-effect sentinels for all four languages remain inert. A Python filename containing shell command syntax remains data. Schema mismatch, escaping entity path and fabricated feature keys are rejected. Shared process tests verify deadline termination, failure, output limits and secret-environment removal.

Security review traced project UUID storage → no-follow bounded source copy → fixed trusted subprocess commands → validated result → atomic owner-scoped persistence. The API accepts no arbitrary filesystem path. Links/special files are rejected, unsupported content is not run, nested archives are not expanded, and code/config/hooks/dependencies from submitted repositories are not executed/installed. No shell command is assembled from source. `subprocess` is confined to the trusted tool runner and the setup-time wrapper compiler. Uploaded Java is never compiled. User paths and tool stderr/stack traces are not returned or logged.

Phase 2 CSRF/authentication/ownership/ZIP/GitHub/storage regression tests remain green. Every analysis route is owner scoped; foreign/missing IDs return 404. Active-run deletion is blocked. Tests cover queue failure after commit, duplicate task lock, redelivery, expiry, safe failure messages, atomic rollback, workspace cleanup, pagination, history and cascaded deletion. No auth/session weakening or source replacement was added.

## Frontend and CI

READY project details expose start, history, status, summary, warnings, language filter, paginated metrics and explicit TypeScript MODEL_UNAVAILABLE. Polling stops on completion/failure/unmount, requests abort on cleanup, and errors can be retried. Summary values/metrics come from persisted API responses. No invented percentages, risk or ML output exists. Existing authentication/project flows remain functional.

CI backend now installs trusted Node/Java tools and checksum-verifies CK, then runs real analyzers and PostgreSQL tests. Frontend checks remain intact. The Docker job now exercises successful mixed-language analysis and failed no-entity runs through Playwright, in addition to migration/readiness/ping checks. Local CI-equivalent commands passed. Hosted CI has not yet verified this revision.

## Phase 3 acceptance matrix

Every criterion from the Phase 3 request is recorded below. PASS is evidence from local implementation/tests unless explicitly hosted.

| Area | Criterion | Result |
|---|---|---|
| Lifecycle | AnalysisRun persisted | PASS |
| Lifecycle | READY project can start analysis | PASS |
| Lifecycle | Analysis is asynchronous | PASS |
| Lifecycle | Celery worker performs analysis | PASS |
| Lifecycle | Statuses transition correctly | PASS |
| Lifecycle | Failures persist safely | PASS |
| Lifecycle | Completed results are immutable | PASS |
| Lifecycle | Retries do not duplicate results | PASS |
| Ownership | Analysis creation owner-scoped | PASS |
| Ownership | Run retrieval owner-scoped | PASS |
| Ownership | Entity retrieval owner-scoped | PASS |
| Ownership | Cross-user access denied | PASS |
| Source safety | Trusted project source path only | PASS |
| Source safety | No arbitrary user filesystem path | PASS |
| Source safety | No symlink traversal | PASS |
| Source safety | No submitted source execution | PASS |
| Source safety | No submitted dependency installation | PASS |
| Source safety | No repository script execution | PASS |
| Java | CK works | PASS |
| Java | Class entities stored | PASS |
| Java | Required CK metrics extracted | PASS |
| Java | LOC represented | PASS |
| Java | Analyzer version stored | PASS |
| Java | Failures/timeouts handled | PASS |
| Python | Radon works | PASS |
| Python | AST parsing works | PASS |
| Python | Function entities stored | PASS |
| Python | Approved metrics extracted | PASS |
| Python | Source never imported | PASS |
| Python | Parse errors handled | PASS |
| JavaScript | Approved parser/analyzer works | PASS |
| JavaScript | File entities stored | PASS |
| JavaScript | Approved metrics extracted | PASS |
| JavaScript | Repository config cannot execute | PASS |
| JavaScript | Source never executes | PASS |
| TypeScript | ts-morph/static parser works | PASS |
| TypeScript | Approved static metrics stored | PASS |
| TypeScript | Source never executes | PASS |
| TypeScript | MODEL_UNAVAILABLE preserved | PASS |
| API | Create analysis endpoint | PASS |
| API | List/get run | PASS |
| API | Paginated entity results | PASS |
| API | Status/summary available | PASS |
| API | Safe errors | PASS |
| Frontend | Start analysis | PASS |
| Frontend | Show analysis progress | PASS — states, no invented percentages |
| Frontend | Show failure | PASS |
| Frontend | Show completed summary | PASS |
| Frontend | Show real static metrics | PASS |
| Frontend | No fake ML/risk output | PASS |
| Database | Migrations apply from clean DB | PASS |
| Database | Phase 2 DB upgrades correctly | PASS |
| Database | Rollback/re-upgrade verified | PASS |
| Database | Useful constraints/indexes exist | PASS |
| Quality | Ruff | PASS |
| Quality | Ruff format | PASS |
| Quality | mypy | PASS |
| Quality | Backend tests | PASS |
| Quality | ESLint | PASS |
| Quality | Prettier | PASS |
| Quality | TypeScript | PASS |
| Quality | Frontend tests | PASS |
| Quality | Production build | PASS |
| Infrastructure | Docker builds | PASS |
| Infrastructure | PostgreSQL healthy | PASS |
| Infrastructure | Redis healthy | PASS |
| Infrastructure | Celery healthy | PASS |
| Infrastructure | Worker includes required trusted analyzers | PASS |
| Infrastructure | Real analysis works in container stack | PASS |
| CI | Phase 3 workflow configured | PASS |
| CI | Hosted CI green | **NOT TESTED — pending** |

## Important file inventory

Created: migration `backend/alembic/versions/f2de3d2ac9dd_static_analysis_runs_and_entities.py`; backend analysis model/schema/API/service; analyzer contracts, discovery, subprocess boundary, launcher, Python/Java/script adapters and trusted tools/locks; Celery analysis task/config; frontend analysis service/panel; analyzer/lifecycle/frontend tests and six inert source fixtures; METRIC_SCHEMAS.md and this report. Infrastructure changes reuse the existing Docker/Compose/CI files; no additional service was created.

Modified: API registration/lifespan, project delete protection, status capability, settings, Celery bootstrap, Alembic imports, Python dependencies/lock, relevant baseline tests; project/workspace/home wording and browser flows; Dockerfile, dockerignore, Compose, CI workflow, env example, gitignore, Makefile; README, AGENT, PROJECT_STATE, TECHNICAL_DECISIONS. Earlier Phase 2 closure changes were retained.

## Limits and next phase

Java grammar is Java 11 and unresolved dependencies can affect CK binding metrics. Unsupported/oversized/binary/malformed input is explicitly skipped or failed; not every valid modern-language construct is promised. Python nested-subtree counts overlap and normalized MI discards comments. JS aggregate complexity and TS decision count are not cross-language equivalents. These constraints are part of schema v1.

Linux subprocess protections and Compose isolation are required for the documented worker behavior. Normal cleanup is verified; hard-kill scratch requires container restart/native orphan recovery. Stale-state cleanup is request-triggered. Admission quotas, production retention/reconciliation and horizontal scaling hardening remain outside this local foundation. Parser tools are trusted dependencies, not a claim of protection against every possible parser vulnerability.

Before Phase 4, confirm hosted CI, then freeze exact tool/runtime/schema semantics for dataset extraction. Dataset feature names alone are insufficient compatibility evidence. Required granularities remain Java class, Python function, JavaScript file; TypeScript remains static-only. Feature ordering and preprocessing must be specified by the future dataset/model contract. No model may be substituted or metrics filled to force inference.
