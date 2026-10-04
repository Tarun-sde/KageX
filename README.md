# KageX

> **AI-Powered Software Defect Prediction & Code Risk Analysis**
>
> **Detect the unseen.**

KageX is a final-year project for language-specific static metrics and validated defect-risk predictions. **Submitted source code must never be executed.**

## Current status

- **Phase 0: COMPLETE / FROZEN.** Architecture, datasets, granularities, and ML integrity rules remain unchanged.
- **Phase 1: Implemented; verification recorded in [PROJECT_STATE](docs/PROJECT_STATE.md).** Hosted CI must be green before formal phase closure.
- **Phase 2: Not started.** Authentication, projects, and secure ingestion are next in the roadmap.

### Implemented

React application shell with `/`, `/app`, and a not-found route; real API/dependency connection status; FastAPI liveness, readiness, and versioned status; PostgreSQL/SQLAlchemy sessions and Alembic; Redis; a Celery ping task; Docker development stack; tests, lint, formatting, strict type checks, and CI configuration.

### Planned

Authentication, ZIP/public GitHub ingestion, analyzers, dataset pipelines, trained models, predictions, explanations, recommendations, and the full interactive dashboard. None of these features is currently available. No mock predictions or model artifacts exist.

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
| Tooling | uv 0.12.23, Ruff, mypy, pytest; ESLint, Prettier, Vitest, Testing Library |
| Node | Node 24 recommended; Node 22.12+ supported within major 22 |

Exact dependency resolutions live in `backend/uv.lock` and `frontend/package-lock.json`. The Redis client version is constrained by Celery's supported dependencies. Tests use `httpx2`, the transport requested by the installed Starlette TestClient, rather than its deprecated `httpx` fallback. Recharts, ML, AST, and 3D packages remain deferred until used. The backend uses synchronous SQLAlchemy sessions; FastAPI runs synchronous routes/dependencies in its thread pool.

Tailwind uses its [official Vite integration](https://tailwindcss.com/docs/installation/using-vite); CSS theme tokens live in `frontend/src/styles/index.css`. The dark shell adapts the reference's orange signal motif, serif hierarchy, subtle depth, and spacing. System fonts (Georgia and system sans fallbacks) avoid external font requests. No prototype scripts or sample metrics were copied. Route sections and isolated visual components leave room for later visual work without introducing WebGL or animation dependencies.

## Quick start: Docker

Requires Docker Engine and Docker Compose v2+.

```bash
cp .env.example .env
docker compose up --build --wait
```

Open [frontend](http://localhost:5173), [workspace](http://localhost:5173/app), or [API documentation](http://localhost:8000/docs).

Compose starts PostgreSQL, Redis, a one-shot migration service, backend, worker, and frontend. Health checks gate dependencies; migration completion gates API/worker startup. Database data survives restarts in the `postgres_data` volume. API and frontend source mounts support hot reload. Rebuild after dependency/configuration changes; rebuild/restart the worker after worker-code edits.

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
| `VITE_API_BASE_URL` | Public browser API origin; blank uses same-origin requests and requires a reverse proxy |

Compose deliberately replaces native database/Redis/Celery URLs with service-network URLs. Container task results use Redis DB 1; the broker uses DB 0. If changing the API host port, update `VITE_API_BASE_URL` as well. If changing the frontend origin, update CORS. `POSTGRES_*` changes do not reconfigure an existing database volume; migrate credentials explicitly. URL-encode special characters in native connection URL credentials; keep the disposable Compose credentials URL-safe.

## API foundation

| Endpoint | Behavior |
|---|---|
| `GET /health` | Lightweight liveness: status, service, version; no dependency I/O |
| `GET /ready` | Executes `SELECT 1` and Redis `PING`; 200 when both work, otherwise 503 with safe booleans |
| `GET /api/v1/status` | `phase: foundation`, `analysis_available: false` |

`/health` and `/ready` are unversioned operational endpoints; application APIs use `/api/v1`. Readiness does not certify worker health or model availability. The workspace checks both endpoints on mount and on **Check again**, with bounded requests and explicit loading/unavailable states.

Errors use `{"error":{"code":"…","message":"…"}}`. Unexpected errors are logged by exception type; responses and logs omit exception messages, request bodies, and secrets. Future routes must use safe HTTP error messages. Future authentication will expand CORS methods deliberately; the foundation allows only GET.

## Database migrations

Revision `0001` establishes Alembic history with no domain tables. The only database table created is Alembic's own version table.

```bash
cd backend
uv run alembic upgrade head
uv run alembic current
uv run alembic check
# Once a later phase adds real models to Base.metadata:
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

Format edits with `uv run ruff format .` in `backend` and `npm run format` in `frontend`. Unit tests do not require running database/Redis services. Infrastructure checks use real PostgreSQL, Redis, migrations, API requests, and a Celery task.

GitHub Actions runs frontend checks/build, backend checks, and Docker integration on pushes and pull requests, with npm/uv caches and read-only repository permissions. Local results do not imply a hosted workflow run has passed.

## Repository structure

```text
.github/workflows/ci.yml
backend/
  app/
    api/                 # operational routes and versioned status
    core/                # typed settings and safe errors
    db/                  # SQLAlchemy base, engine, session dependency
    workers/             # Celery and harmless ping task
    main.py              # application factory and resource lifecycle
  alembic/versions/      # minimal migration baseline
  tests/
  pyproject.toml
  uv.lock
  Dockerfile
frontend/
  src/
    app/                 # routing and shared page layout
    components/          # panel and live connection status
    pages/               # overview and foundation workspace
    services/            # typed, validated API responses
    styles/              # Tailwind and design tokens
  tests/
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

No source upload, extraction, cloning, or execution path exists. Future analysis must parse untrusted source statically in isolated workspaces. Never execute source, install dependencies, run tests, or trigger build hooks from submitted repositories. No prediction may be fabricated; incompatible or missing models must produce an explicit unavailable state.

- [Engineering contract](AGENT.md)
- [Current state and verification](docs/PROJECT_STATE.md)
- [Frozen implementation roadmap](docs/FINAL_IMPLEMENTATION_PLAN.md)
- [Frozen technical decisions](docs/TECHNICAL_DECISIONS.md)
- [Design direction](docs/DESIGN.md), [design reference](docs/DESIGN_REFERENCE.md), [visual-only prototype](docs/design.html)

The retained visual prototype contains its original Axisflow branding and demo figures. It is documentation only and is not served by the application. License selection remains pending before final release.
