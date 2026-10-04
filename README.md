# KageX

> **AI-Powered Software Defect Prediction & Code Risk Analysis**
>
> **Detect the unseen.**

KageX is a final-year project for language-specific static metrics and validated defect-risk predictions. **Submitted source code must never be executed.**

## Current status

- **Phase 0: COMPLETE / FROZEN.** Architecture, datasets, granularities, and ML integrity rules remain unchanged.
- **Phase 1: COMPLETE / FROZEN.** Hosted CI success confirmed by the project owner.
- **Phase 2: COMPLETE.** Local verification and the hosted GitHub Actions workflow are green; evidence is recorded in [PROJECT_STATE](docs/PROJECT_STATE.md) and [Phase 2 verification](docs/PHASE_2_VERIFICATION.md).
- **Phase 3: COMPLETE / FROZEN.** The project owner confirmed hosted CI is green. See [Phase 3 verification](docs/PHASE_3_VERIFICATION.md) and [metric contracts](docs/METRIC_SCHEMAS.md).
- **Phase 4A: COMPLETE / FROZEN.** The project owner confirmed hosted CI is green for commit `7bbf452`. Scoped dataset acquisition, independent PyTraceBugs recovery verification, and local audits pass. See [dataset audit](docs/PHASE_4A_DATASET_AUDIT.md) and [feature candidates](docs/PHASE_4A_FEATURE_REFERENCE.md). Phase 4B is READY.

### Implemented

Registration/login with expiring server sessions; protected project CRUD; bounded ZIP/public GitHub ingestion; queued Java/Python/JavaScript/TypeScript static analysis; persisted run history, summaries, warnings and paginated versioned metrics; PostgreSQL/Alembic, Redis/Celery, Docker, tests and CI.

### Planned

Dataset pipelines, trained models, predictions, explanations, recommendations, and the full analysis dashboard remain future work. No mock predictions or model artifacts exist.

| Language | Planned granularity | Frozen prediction strategy |
|---|---|---|
| Java | Class | Separate validated model; PROMISE/Jureczko + approved D'Ambros; CK + LOC |
| Python | Function | Separate validated model; BugsInPy/PyTraceBugs; Radon + AST |
| JavaScript | File | Separate validated model; BugsJS; ESLint + approved AST tools |
| TypeScript | File/static analysis | `MODEL_UNAVAILABLE`; never substitute the JavaScript model |

## Architecture and versions

```text
React / Vite → FastAPI → PostgreSQL
                  └──→ Redis ← Celery worker
```

| Area | Selected foundation |
|---|---|
| Frontend | React 19.3, React Router 7.18, Vite 8.3, Tailwind 4.3 |
| TypeScript | 6.0.3 (current typescript-eslint supports versions below 6.1) |
| Backend | Python 3.14, FastAPI 0.142, Pydantic 2.13, SQLAlchemy 2.1, Psycopg 3.3, Alembic 1.20 |
| Infrastructure | PostgreSQL 18, Redis 8 server / Redis 6.4 Python client, Celery 5.6 |
| Tooling | uv 0.12.23, Ruff, mypy, pytest; ESLint, Prettier, Vitest, Testing Library, Playwright |
| Node | Node 24 recommended; Node 22.12+ supported within major 22 |

Exact dependency resolutions live in `backend/uv.lock`, `frontend/package-lock.json`, and `backend/app/analyzers/tools/package-lock.json`. Analyzers use Radon 6.0.1, CK 0.7.0, ESLint 10.12.0 and ts-morph 28.0.0 (TypeScript parser 6.0.2). The Redis client version is constrained by Celery's supported dependencies. Tests use `httpx2`, the transport requested by the installed Starlette TestClient. Recharts, ML and 3D packages remain deferred. SQLAlchemy sessions are synchronous; FastAPI runs synchronous routes/dependencies in its thread pool.

Tailwind uses its [official Vite integration](https://tailwindcss.com/docs/installation/using-vite); CSS theme tokens live in `frontend/src/styles/index.css`. The dark shell adapts the reference's orange signal motif, serif hierarchy, subtle depth, and spacing. System fonts (Georgia and system sans fallbacks) avoid external font requests. No prototype scripts or sample metrics were copied. Route sections and isolated visual components leave room for later visual work without introducing WebGL or animation dependencies.

## Quick start: Docker

Requires Docker Engine and Docker Compose v2+.

```bash
cp .env.example .env
docker compose up --build --wait
```

Open [frontend](http://localhost:5173), [workspace](http://localhost:5173/app), or [API documentation](http://localhost:8000/docs).

Compose starts PostgreSQL, Redis, a one-shot migration service, backend, worker, and frontend. Health checks gate dependencies; migration completion gates API/worker startup. Database data survives restarts in `postgres_data`; source files survive in the separate private `source_data` volume. API and frontend source mounts support hot reload. Rebuild after dependency/configuration changes; rebuild/restart the worker after worker-code edits.

```bash
docker compose ps
docker compose logs backend worker
docker compose exec -T backend python -c "from app.workers.celery_app import ping; print(ping.delay().get(timeout=20))"
docker compose down
```

The ping should print `pong`. Development services bind to loopback on the host. This is a development stack, not a production deployment. No deployment is configured. Plain `docker compose up` also works with disposable defaults; the copied `.env` is needed for the documented native setup.

## Local development without application containers

Install Node 24 and [uv](https://docs.astral.sh/uv/getting-started/installation/). Use uv as the only Python dependency manager. Run from the repository root unless noted.

```bash
cp .env.example .env
# Or use existing local PostgreSQL 18 / Redis 8 instances and adjust .env.
docker compose up -d --wait postgres redis
cd backend
uv sync --locked
npm ci --ignore-scripts --prefix app/analyzers/tools
# Requires a trusted JDK 17+ with javac; compiles only KageX's wrapper.
uv run python app/analyzers/tools/install_ck.py
uv run alembic upgrade head
uv run python -m app
```

In another terminal:

```bash
cd backend
uv run celery -A app.workers.celery_app:celery_app worker --loglevel=INFO --concurrency=1
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Python reads the root `.env` regardless of working directory. Vite also loads the root `.env`; restart Vite after changing it. Avoid running native and container frontends/APIs on the same ports simultaneously.

Native analyzer workers require Linux, Java 17+ and Node 24.14.0 (tested also on Node 22.23.1). `ANALYZER_JAVA` and `ANALYZER_NODE` default to `/usr/bin/java` and `/usr/bin/node`; set absolute paths if your tools are elsewhere. Only KageX's locked dependencies are installed, never those of submitted repositories. Docker builds the wrapper and includes Java/Node tools only in the worker image. Native workers need equivalent operator-managed memory/process isolation; Compose supplies these limits.

## Environment

Only `.env.example` is version-controlled. `.env` is ignored. Example credentials are disposable local values, not real service credentials.

| Variable | Meaning |
|---|---|
| `APP_ENV` | `development`, `test`, or `production`; development enables native API reload |
| `BACKEND_HOST` | Native API bind host; Compose binds inside its network on `0.0.0.0` |
| `BACKEND_PORT` | Native API port and Compose host API port (container port stays 8000) |
| `FRONTEND_URL` | Validated public frontend origin for future links; CORS is configured separately |
| `CORS_ALLOWED_ORIGINS` | JSON array of explicit HTTP(S) origins; wildcards rejected |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Compose database provisioning and container connection settings |
| `DATABASE_URL` | Required native SQLAlchemy URL using `postgresql+psycopg://` |
| `REDIS_URL` | Required native Redis URL (`redis://` or `rediss://`) |
| `CELERY_BROKER_URL` | Optional native broker override; blank falls back to `REDIS_URL` |
| `CELERY_RESULT_BACKEND` | Optional native result store override; blank falls back to `REDIS_URL` |
| `SESSION_TTL_SECONDS` | Absolute session lifetime, default 3600; range 60–86400 |
| `PROJECT_STORAGE_ROOT` | Native absolute directory; default `.data/sources`; Compose fixes `/app/storage` |
| `MAX_UPLOAD_SIZE_MB` | Compressed upload/GitHub limit, default 25 MiB |
| `MAX_EXTRACTED_SIZE_MB` | Total expanded limit, default 100 MiB |
| `MAX_FILE_SIZE_MB` | Individual file limit, default 10 MiB |
| `MAX_ARCHIVE_FILES` | Maximum ZIP entries including directories, default 2000 |
| `MAX_COMPRESSION_RATIO` | Maximum expansion ratio per entry, default 100 |
| `INGESTION_TIMEOUT_SECONDS` | Preparation deadline, default 30 seconds; network operations also limited to 5 seconds |
| `ANALYSIS_TIMEOUT_SECONDS` | Total analysis deadline, default 120 seconds; Celery soft/hard limits add 10/20 seconds |
| `ANALYSIS_QUEUE_TIMEOUT_SECONDS` | Queue expiry, default 600 seconds |
| `ANALYZER_TIMEOUT_SECONDS` | Per-language tool deadline, default 45 seconds |
| `MAX_ANALYSIS_FILE_BYTES` | Per-file parsing limit, default 524288; larger files get warnings |
| `MAX_ANALYSIS_ENTITIES` | Maximum entities per run, default 10000 |
| `MAX_ANALYZER_OUTPUT_BYTES` | Tool stream output limit, default 8388608 |
| `TEST_DATABASE_URL` | Export for pytest; default disposable local PostgreSQL URL |
| `VITE_API_BASE_URL` | Public browser API origin; blank uses same-origin requests and requires a reverse proxy |

Compose deliberately replaces native database/Redis/Celery URLs with service-network URLs. Container task results use Redis DB 1; the broker uses DB 0. If changing the API host port, update `VITE_API_BASE_URL` as well. If changing the frontend origin, update CORS. `POSTGRES_*` changes do not reconfigure an existing database volume; migrate credentials explicitly. URL-encode special characters in native connection URL credentials; keep the disposable Compose credentials URL-safe.

## API foundation

| Endpoint | Behavior |
|---|---|
| `GET /health` | Lightweight liveness: status, service, version; no dependency I/O |
| `GET /ready` | Executes `SELECT 1` and Redis `PING`; 200 when both work, otherwise 503 with safe booleans |
| `GET /api/v1/status` | `phase: static_analysis`, `analysis_available: true`; capability, not a worker health guarantee |

`/health` and `/ready` are unversioned operational endpoints; application APIs use `/api/v1`. Readiness does not certify worker health or model availability. The workspace checks both endpoints on mount and on **Check again**, with bounded requests and explicit loading/unavailable states.

Errors use `{"error":{"code":"…","message":"…"}}`. Unexpected errors are logged by exception type; responses and logs omit exception messages, request bodies, and secrets. Future routes must use safe HTTP error messages. CORS allows explicit trusted origins with credentials and the implemented GET/POST/PATCH/DELETE methods. Unsafe auth/project requests require both the trusted `Origin` and `X-KageX-Request: 1`.

## Authentication and project API

Open `/register`, create an account, then create a ZIP or GitHub project in `/app`. Submit its source on the detail page. `READY` means **source prepared**, never analysis complete. Rename and delete are available there; deletion removes stored source. Failed ingestion can be retried on the same project; a successful source is immutable, so create another project for a new snapshot.

| Endpoint under `/api/v1` | Contract |
|---|---|
| `POST /auth/register` | `{email,password}`; 201, establishes session |
| `POST /auth/login` | `{email,password}`; 200, rotates current session |
| `GET /auth/me` | Safe `{id,email}`; 401 when absent/expired |
| `POST /auth/logout` | Revokes current server session; 204 |
| `POST /projects` | `{name,source_type: "ZIP_UPLOAD" or "GITHUB"}`; 201 |
| `GET /projects?offset=0` | Owner-scoped array; at most 50 per page |
| `GET /projects/source-limits` | Authenticated browser upload limit |
| `GET /projects/{id}` | Owner-scoped project metadata |
| `PATCH /projects/{id}` | `{name}` only |
| `DELETE /projects/{id}` | Owner-scoped record/source deletion; 204 |
| `POST /projects/{id}/source/zip` | **Raw ZIP body**, `Content-Type: application/zip`; not multipart |
| `POST /projects/{id}/source/github` | `{url:"https://github.com/owner/repository"}` |

## Static analysis

On a READY project, select **Start static analysis**. The API commits QUEUED before publishing the run UUID to Celery; the worker transitions RUNNING → COMPLETED or FAILED. READY continues to mean source prepared. At most one active run per project is permitted; deletion is blocked during active analysis. A new run is the explicit retry mechanism. Completed metrics do not change.

| Endpoint under `/api/v1/projects/{project_id}` | Contract |
|---|---|
| `POST /analyses` | Owner-only; no source/path body; returns 202 with persisted run |
| `GET /analyses?offset=0` | Owner-only history, up to 50 runs |
| `GET /analyses/{run_id}` | Status, timestamps, safe failure, summary, warnings |
| `GET /analyses/{run_id}/entities?offset=0&limit=50&language=python` | Owner-only paginated metrics; limit 1–100, optional supported-language filter |

The project page polls active runs every two seconds, stops at terminal status or unmount, shows safe failures and real metrics, and supports history/language/entity pagination. TypeScript displays `MODEL_UNAVAILABLE`. There is no ML output for any language. Supported files, exact feature names and semantics, analyzer/runtime versions, limitations and isolation are documented in [METRIC_SCHEMAS.md](docs/METRIC_SCHEMAS.md).

Redis carries UUID-only task messages; PostgreSQL is the authoritative result store. Late acknowledgement and advisory locking make redelivery safe. Tool errors persist FAILED without partial entities; syntax errors can produce COMPLETED with warnings. Expired queued/running jobs become FAILED on run reads, new analysis, or project deletion. There is no periodic sweeper. Normal temporary data is removed on success/failure; after a hard crash, restart the worker container to discard its bounded private tmpfs. With native workers stopped, remove only confirmed orphan `kagex-analysis-*` directories. Source snapshots follow the Phase 2 retention rule below.

Use cookies (`credentials: include` in the browser), `Origin: <trusted frontend origin>`, and `X-KageX-Request: 1` for writes. Ownership/status/storage fields supplied by clients are rejected. Missing and foreign projects both return 404; conflicting concurrent writes return 409 `PROJECT_BUSY`. Validation returns a safe 422 envelope. Domain failures return stable codes without filesystem paths.

Passwords are Argon2id hashes (12–128 characters). Random opaque session tokens exist only in HttpOnly cookies; the database stores SHA-256 token digests. Default expiry is one hour, without sliding refresh. Development cookies work on localhost HTTP. Production requires `APP_ENV=production`, explicit HTTPS origins, and HTTPS termination; cookies become Secure, host-only `__Host-kagex_session`. Deploy UI/API on the same site for SameSite=Lax behavior. No JWT signing key, refresh-token endpoint, or browser storage credential is needed.

ZIP and GitHub intake share the same extractor. Only normal stored/deflated ZIP archives with regular files/directories are accepted; encrypted, ZIP64, split/self-extracting layouts, traversal, symlinks, special files, conflicting paths, malformed archives, and excessive resources are rejected. Nested ZIPs/binaries are retained as opaque bytes, never recursively extracted or analyzed. Public GitHub default-branch snapshots download from fixed `codeload.github.com` without redirects, credentials, Git hooks, or repository dependency installation; private repos, custom hosts, branch URLs, and tokens are unsupported.

Ingestion is synchronous and bounded for Phase 2; the UI shows preparation activity without fabricated percentage progress. Normal success/failure removes temporary archives/staging. Prepared source remains locally until project deletion, an explicit development retention policy. Source is never served as web content. A process/host crash can leave staging, orphan source, or deletion quarantine; stop the API and reconcile the private storage with project records before cleanup. Do not delete the volume to resolve one failed upload. Production retention, crash reconciliation, authentication throttling, and per-user storage quotas remain deployment hardening work; this Compose stack is for local development.

## Database migrations

Revision `0001` is the empty foundation baseline; `6e605e1f5bed` adds users, hashed server sessions, and owner-scoped projects. `f2de3d2ac9dd` adds analysis runs/entities, cascading foreign keys, active-run uniqueness, entity identity uniqueness and query indexes. Downgrading Phase 3 removes analysis history and metrics while retaining Phase 2 account/project data.

```bash
cd backend
uv run alembic upgrade head
uv run alembic current
uv run alembic check
# After changing model metadata:
uv run alembic revision --autogenerate -m "describe the schema change"
```

Import future models into Alembic's environment before autogeneration and review every generated migration. Do not replace migrations with `create_all()` at API startup. `app/db/session.py` provides the engine, declarative base, and request session dependency; future services own transaction/commit decisions.

## Checks

```bash
make install
make check
```

The Makefile shortcuts require GNU Make. If it is unavailable, run the equivalent commands explicitly:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

```bash
cd frontend
npm run lint
npm run format:check
npm run typecheck
npm test
npm run build
```

For browser tests, first run the full Compose stack:

```bash
cd frontend
npx playwright install --with-deps chromium
npm run test:e2e
```

The tests exercise real HTTP cookies, registration/login, CRUD, malicious ZIP rejection, retry, source persistence, analysis failure, and successful four-language Celery analysis at desktop/mobile widths. They create unique disposable test accounts and delete successful test projects; accounts and failed-test artifacts may remain for inspection. Do not run them against a production service. The browser fixture builder needs Python 3 and only archives inert fixture bytes.

Format edits with `uv run ruff format .` in `backend` and `npm run format` in `frontend`. Backend integration tests require PostgreSQL and create/drop isolated randomly named schemas using migrations. The default test URL uses the disposable Compose credentials; export `TEST_DATABASE_URL` for another test database. The test database account needs schema creation permission. Redis is only required for live infrastructure checks. Infrastructure checks use real PostgreSQL, Redis, migrations, API requests, and a Celery task.

GitHub Actions runs frontend checks/build, backend checks against a PostgreSQL service (including clean migration round trips), and Docker integration plus Playwright on pushes and pull requests, with npm/uv caches and read-only repository permissions. Local results do not imply a hosted workflow run has passed.

## Repository structure

```text
.github/workflows/ci.yml
backend/
  app/
    api/                 # auth, projects, ingestion, analysis, operational endpoints
    analyzers/           # contracts, safe discovery/process boundary, trusted tools
    core/                # typed settings and safe errors
    db/                  # SQLAlchemy base, engine, session dependency
    models/              # User, AuthSession, Project, AnalysisRun, AnalysisEntity
    schemas/             # validated public API contracts
    services/            # ingestion, storage, analysis lifecycle/publication
    workers/             # Celery analysis and harmless ping task
    main.py              # application factory and resource lifecycle
  alembic/versions/      # baseline, Phase 2, Phase 3 migrations
  tests/
  pyproject.toml
  uv.lock
  Dockerfile
frontend/
  src/
    app/                 # routing and shared page layout
    components/          # panel and live connection status
    pages/               # overview, sign in/up, owned projects
    services/            # typed, validated API responses
    styles/              # Tailwind and design tokens
  tests/
  e2e/                  # desktop/mobile critical browser flows
  package.json
  package-lock.json
  Dockerfile
docs/                    # frozen roadmap, decisions, design, current state
.env.example
.gitignore
docker-compose.yml
Makefile
AGENT.md
README.md
```

## Security and project documents

ZIP and public GitHub archives are stored as inert files in isolated project directories. Trusted analyzers parse bounded copies in private worker workspaces. Never execute source, install dependencies, run tests, or trigger build hooks from submitted repositories. No prediction may be fabricated; incompatible or missing models must produce an explicit unavailable state.

- [Engineering contract](AGENT.md)
- [Current state and verification](docs/PROJECT_STATE.md)
- [Frozen implementation roadmap](docs/FINAL_IMPLEMENTATION_PLAN.md)
- [Frozen technical decisions](docs/TECHNICAL_DECISIONS.md)
- [Design direction](docs/DESIGN.md), [design reference](docs/DESIGN_REFERENCE.md), [visual-only prototype](docs/design.html)

The retained visual prototype contains its original Axisflow branding and demo figures. It is documentation only and is not served by the application. License selection remains pending before final release.
