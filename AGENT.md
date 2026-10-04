# AGENT.md — KageX Engineering Contract

> **Project:** KageX — AI-Powered Software Defect Prediction & Code Risk Analysis  
> **Tagline:** Detect the unseen.  
> **Status:** Final pre-Phase-1 instructions  
> **Location:** Repository root (`/AGENT.md`)

This file is the operating contract for every AI coding agent and developer working on KageX. The objective is to build the planned system in controlled phases while preserving architecture, security, ML validity, design consistency, reproducibility, and documentation.

---

## 1. Mandatory Reading Order

Before changing code, read these files in this order:

1. `AGENT.md`
2. `docs/PROJECT_STATE.md`
3. `docs/FINAL_IMPLEMENTATION_PLAN.md`
4. `docs/TECHNICAL_DECISIONS.md`
5. `docs/DESIGN.md`
6. `docs/DESIGN_REFERENCE.md`
7. `docs/design.html`
8. `README.md`

Do not begin implementation until the current phase and task are clear.

If a referenced file is missing, do not invent its contents. Report the mismatch if it affects the requested work.

---

## 2. Source-of-Truth Priority

If project documents appear to conflict, use this priority:

1. Security and data-integrity requirements
2. `AGENT.md`
3. `docs/TECHNICAL_DECISIONS.md`
4. `docs/FINAL_IMPLEMENTATION_PLAN.md`
5. `docs/PROJECT_STATE.md`
6. `docs/DESIGN.md`
7. `docs/DESIGN_REFERENCE.md`
8. `docs/design.html`
9. `README.md`
10. Existing implementation details

Important distinction:

- `docs/DESIGN.md` defines intended UX/UI behavior.
- `docs/DESIGN_REFERENCE.md` defines reusable visual guidance/tokens.
- `docs/design.html` is the visual prototype/reference implementation.

If `design.html` contains placeholder data or demo behavior, treat it only as visual reference. Never convert demo values into production logic.

---

## 3. Project State and Phase Discipline

Always inspect `docs/PROJECT_STATE.md` before starting work.

At the beginning of Phase 1, the expected state is:

```text
Phase 0: COMPLETE / FROZEN
Phase 1: READY TO START
```

Do not skip phases unless the project owner explicitly changes the roadmap.

Do not mark a phase complete until its Definition of Done in `docs/FINAL_IMPLEMENTATION_PLAN.md` is satisfied.

---

## 4. Project Identity

KageX is an interactive web application that:

1. accepts source projects through ZIP upload or public GitHub import,
2. safely performs static analysis,
3. detects supported languages,
4. extracts language-specific software metrics,
5. matches metrics to a compatible validated ML model,
6. predicts defect risk where a valid model exists,
7. explains supported predictions,
8. provides inspection/refactoring recommendations,
9. stores analysis history,
10. presents results through an interactive dashboard.

**KageX must never execute uploaded project code.**

---

## 5. Frozen Technology Stack

Do not replace core technologies during ordinary implementation.

### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Recharts

### Backend
- FastAPI
- Pydantic
- PostgreSQL
- Redis
- Celery

### ML / Data
- Python
- Pandas
- scikit-learn
- XGBoost where justified
- imbalanced-learn where justified
- SHAP where technically compatible
- Joblib or native model serialization where appropriate

### Quality
- pytest
- Ruff
- mypy
- ESLint
- TypeScript type checking
- Vitest / React Testing Library
- Playwright for critical E2E flows
- GitHub Actions

Do not replace a frozen core technology merely because another tool is newer or easier.

---

## 6. Language and Model Contract

KageX does **not** use one universal model for every language.

| Language | Analysis Level | Metric Direction | Prediction |
|---|---|---|---|
| Java | Class | CK + LOC-related metrics | Supported with compatible validated model |
| Python | Function | Radon + AST-derived metrics | Supported with compatible validated model |
| JavaScript | File | Static parser/AST-derived metrics | Supported with compatible validated model |
| TypeScript | File/static analysis | ts-morph/static metrics | `MODEL_UNAVAILABLE` until validated model exists |

Never silently substitute a model from another language.

Never fabricate a prediction.

---

## 7. TypeScript Rule

TypeScript static analysis is allowed.

TypeScript defect prediction is **not** allowed until a validated compatible TypeScript dataset/model has been formally added.

Expected behavior:

```json
{
  "prediction_status": "MODEL_UNAVAILABLE",
  "language": "typescript",
  "reason": "No validated compatible TypeScript defect model is available."
}
```

Never return a fake probability such as `0.0`, `0.5`, a random value, a hard-coded demo value, or JavaScript-model output for TypeScript.

---

## 8. Static-Analysis-Only Security Rule

Submitted repositories are untrusted input.

Never:

- execute uploaded Python files,
- execute Java classes,
- execute JavaScript or TypeScript files,
- import user source into the application runtime,
- run user tests,
- run repository scripts,
- run Git hooks,
- run `npm install` inside submitted repositories,
- run package lifecycle scripts,
- run arbitrary Maven/Gradle build tasks merely for analysis,
- execute shell commands derived from repository content.

If an analyzer requires source execution, redesign the analyzer.

---

## 9. Secure Ingestion Rules

ZIP upload and public GitHub import must converge into one common post-ingestion pipeline.

### ZIP input must defend against
- Zip Slip / path traversal
- absolute paths
- symlink abuse
- decompression bombs
- oversized archives
- excessive file counts
- malformed archives
- unsafe filenames

### GitHub input
Initial supported scope is public GitHub repositories.

Validate:
- URL scheme
- hostname
- repository structure
- download size
- time/resource limits

Do not execute repository hooks or scripts.

### Temporary workspace
Every analysis must use an isolated temporary workspace.

Never:
- serve the workspace publicly,
- expose filesystem paths through API responses,
- retain temporary source indefinitely,
- reuse one unsafe shared workspace for concurrent analyses.

---

## 10. Authentication and Secrets

User-owned projects and analyses require authentication and authorization.

Rules:
- hash passwords using a modern password hashing mechanism,
- never log passwords,
- never log auth tokens,
- never hardcode secrets,
- never commit `.env`,
- commit only `.env.example`,
- enforce ownership on every user-owned resource,
- avoid long-lived credentials in browser `localStorage`.

Do not weaken authentication for development convenience.

---

## 11. Architecture Boundaries

### Frontend owns
- presentation
- user interaction
- form validation
- routing
- API calls
- loading/error/empty states
- charts and tables
- filtering/search
- responsive behavior

### Backend owns
- authentication and authorization
- ingestion
- static analysis
- metric normalization
- model compatibility
- preprocessing
- inference
- risk calculation
- explanations
- recommendations
- persistence
- job orchestration

### ML pipelines own
- dataset loading
- feature construction
- training
- evaluation
- calibration where needed
- artifact creation
- artifact metadata

The frontend must never reimplement trusted ML preprocessing or alter backend probabilities.

---

## 12. Design Implementation Rules

`docs/design.html` is a **visual reference**, not production architecture.

When implementing the React frontend:

1. preserve the overall visual identity,
2. reproduce layout, spacing, hierarchy, typography, components, and interaction intent,
3. convert repeated UI into reusable React components,
4. use Tailwind rather than blindly copying all prototype CSS,
5. replace hard-coded prototype data with typed API-driven data,
6. keep accessibility and responsive behavior,
7. implement loading, empty, error, and unavailable states,
8. preserve `MODEL_UNAVAILABLE` visibly where applicable.

Do not:
- embed the entire prototype as one React component,
- use `dangerouslySetInnerHTML` simply to reuse `design.html`,
- preserve fake/demo data as application truth,
- duplicate large CSS blocks when reusable components/Tailwind are appropriate.

If exact visuals conflict with accessibility, security, or functional correctness, prioritize correctness and document the small deviation.

---

## 13. UI Consistency Rule

Before adding a frontend component, inspect:

- `docs/DESIGN.md`
- `docs/DESIGN_REFERENCE.md`
- `docs/design.html`

Reuse existing patterns before creating new ones.

Keep consistent:
- page width
- spacing
- typography hierarchy
- border radius
- navigation
- button hierarchy
- cards
- tables
- status badges
- risk labels
- charts
- responsive behavior
- hover/focus states

Avoid introducing unrelated visual styles.

Risk must never be communicated by color alone. Always include readable text such as `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`, or `MODEL UNAVAILABLE`.

---

## 14. Analyzer Architecture

Do not build one giant analyzer containing all language logic.

Use a registry/plugin-style architecture.

Conceptually:

```python
class Analyzer(Protocol):
    language: str
    schema_version: str

    def supports(self, path: Path) -> bool:
        ...

    def analyze(self, workspace: Path) -> list[MetricRecord]:
        ...
```

Each analyzer must:
- identify its language,
- identify component granularity,
- identify schema version,
- preserve relative paths,
- return deterministic structured records where possible,
- report warnings explicitly,
- avoid source execution,
- have fixture-based tests.

---

## 15. Metric Schema Contract

Metric records must be versioned.

Conceptual record:

```text
analysis_run_id
language
component_type
component_id
relative_path
schema_version
metrics
analyzer_version
warnings
```

A model is compatible only when these match:

```text
language
component_type
metric schema version
required feature names
feature ordering
preprocessing expectations
```

Never reorder model features implicitly.

Never fill missing required production features with arbitrary values just to force inference.

---

## 16. Model Registry

Model loading must be centralized.

Conceptual key:

```text
(language, component_type, metric_schema_version)
```

Conceptual result:

```text
compatible model artifact
OR
MODEL_UNAVAILABLE
```

Model metadata should include:
- model ID/version,
- language,
- component level,
- schema version,
- feature names and order,
- preprocessing version,
- training dataset/version,
- algorithm,
- validation metrics,
- threshold/risk-policy version,
- useful dependency/runtime metadata.

Do not scatter model-loading logic across API routes.

---

## 17. ML Integrity Rules

Never:
- fabricate predictions,
- train using production uploads,
- silently use one language model for another,
- fit preprocessing on final test data,
- tune on final test data,
- report training performance as final validation,
- describe probability as certainty,
- silently ignore schema mismatch,
- alter feature ordering,
- hide failed validation.

Evaluation should preserve the frozen project methodology, including appropriate use of:
- PR-AUC
- ROC-AUC
- F1
- MCC
- Brier score
- project/version-aware splitting where applicable
- cross-project validation where feasible

---

## 18. Prediction Contract

Supported prediction example:

```json
{
  "prediction_status": "PREDICTED",
  "language": "java",
  "component_type": "class",
  "probability": 0.73,
  "risk_level": "HIGH",
  "model_version": "java_defect_v1",
  "schema_version": "java_ck_v1"
}
```

Unsupported example:

```json
{
  "prediction_status": "MODEL_UNAVAILABLE",
  "language": "typescript",
  "probability": null,
  "risk_level": null,
  "reason": "No validated compatible TypeScript defect model is available."
}
```

Use explicit states instead of overloading `null`.

---

## 19. Risk, Explainability, and Recommendations

Possible user-facing risk levels:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Rules:
- thresholds belong to backend/domain logic,
- thresholds must be versioned,
- frontend must not maintain independent thresholds,
- probability is not confirmed defect presence.

Use SHAP only where technically valid for the selected model/pipeline.

Explanations must reference real model features and avoid causal claims.

Acceptable:

> High complexity and coupling contributed to the model's higher predicted defect risk.

Not acceptable:

> Complexity caused a bug in this file.

Initial recommendations should be deterministic and rule-based. They should suggest investigation/refactoring, not claim a specific runtime bug has been found.

---

## 20. Analysis Job States

Use explicit asynchronous states such as:

```text
QUEUED
INGESTING
DETECTING_LANGUAGES
ANALYZING
PREDICTING
EXPLAINING
COMPLETED
COMPLETED_WITH_WARNINGS
FAILED
```

Requirements:
- persist failures,
- preserve useful warnings,
- provide safe user-facing messages,
- never return internal stack traces in normal API responses.

---

## 21. Error Categories

Prefer explicit domain errors such as:

```text
INVALID_UPLOAD
ARCHIVE_TOO_LARGE
UNSAFE_ARCHIVE
INVALID_GITHUB_URL
REPOSITORY_TOO_LARGE
NO_SUPPORTED_SOURCE
ANALYZER_FAILED
MODEL_UNAVAILABLE
SCHEMA_MISMATCH
INFERENCE_FAILED
UNAUTHORIZED
FORBIDDEN
INTERNAL_ERROR
```

Do not swallow errors with:

```python
except Exception:
    pass
```

At system boundaries, broad exception handling must:
1. log safe technical context,
2. preserve failure state,
3. return a controlled user-facing error.

---

## 22. Backend Code Rules

Prefer:
- small route handlers,
- Pydantic schemas,
- service/domain layers,
- typed functions,
- dependency injection where useful,
- explicit configuration,
- migrations,
- structured logging,
- testable modules.

Avoid:
- business logic directly inside route handlers,
- hidden global state,
- duplicated validation,
- magic constants,
- circular imports,
- oversized service modules.

Do not put model training logic in API routes.

---

## 23. Frontend Code Rules

Use strict TypeScript.

Prefer:
- reusable components,
- feature-oriented modules,
- typed API clients,
- typed response models,
- route-level pages,
- predictable state,
- accessible interactions,
- responsive layout.

Avoid:
- unnecessary `any`,
- giant page components,
- duplicated API calls,
- hidden error states,
- fake production data,
- frontend-owned ML logic.

Every async screen must consider:

```text
loading
success
empty
error
unavailable
```

---

## 24. Database Rules

Use explicit relational entities and migrations.

Expected concepts include:
- User
- Project
- RepositorySource
- AnalysisRun
- ComponentMetric
- Prediction
- Explanation
- Recommendation

Rules:
- enforce ownership,
- use foreign keys,
- use timezone-aware timestamps,
- retain schema/model versions,
- use JSON only where flexible metric data genuinely benefits from it,
- do not store secrets unnecessarily.

---

## 25. Logging Rules

Safe logs may include:
- analysis ID,
- project ID,
- analysis stage,
- duration,
- language,
- analyzer/version,
- model/version,
- warning/error category.

Never log:
- passwords,
- secret keys,
- access tokens,
- refresh tokens,
- complete private source files,
- environment secrets.

---

## 26. Testing Is Part of Implementation

Tests are not postponed until the final phase.

### Backend
Test:
- health/configuration,
- authentication,
- authorization,
- ingestion security,
- analyzer registry,
- language analyzers using fixtures,
- schema compatibility,
- model registry,
- preprocessing,
- inference,
- risk policy,
- recommendations,
- task orchestration,
- API behavior.

### Frontend
Test:
- forms,
- validation,
- loading states,
- error states,
- empty states,
- unavailable states,
- risk table behavior,
- filters/search,
- model-unavailable presentation,
- critical API interactions.

### E2E
Protect important flows such as:

```text
authenticate
-> create project
-> submit repository
-> observe analysis
-> inspect result
-> inspect risky component
-> view explanation/recommendation
```

---

## 27. Canonical Verification Commands

Run the relevant checks before declaring work complete.

### Backend

```bash
ruff check .
mypy .
pytest
```

### Frontend

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

Run E2E tests when a change affects a critical end-to-end workflow.

Never claim a command passed if it was not actually executed.

---

## 28. Dependency Rules

Before adding a dependency:

1. confirm the existing stack cannot reasonably handle the requirement,
2. prefer a maintained package,
3. check license suitability,
4. avoid redundant packages,
5. pin/version appropriately,
6. document setup changes.

Do not add dependencies for trivial utilities that can be implemented clearly and safely.

---

## 29. Git Rules

Keep commits focused.

Suggested style:

```text
feat(backend): add health endpoint
feat(frontend): create application shell
feat(ingestion): reject unsafe archive paths
feat(analyzer): add python metric adapter
feat(ml): register java defect model v1
fix(auth): enforce project ownership
test(ingestion): cover zip slip rejection
docs(project): update phase status
```

Never commit:
- `.env`,
- credentials,
- tokens,
- temporary submitted repositories,
- build output,
- caches,
- oversized datasets without an explicit storage strategy.

---

## 30. Documentation Update Rules

Documentation is part of the product.

Update documentation when changing:
- architecture,
- environment variables,
- setup commands,
- API contracts,
- database behavior,
- analyzer schemas,
- model versions,
- risk thresholds,
- security behavior,
- supported languages,
- phase status.

Use:

```text
docs/TECHNICAL_DECISIONS.md  -> important technical decisions
docs/PROJECT_STATE.md        -> current implementation state/progress
docs/FINAL_IMPLEMENTATION_PLAN.md -> roadmap and phase definitions
```

Do not turn `README.md` into a duplicate of every technical document.

---

## 31. PROJECT_STATE.md Update Rule

After a meaningful completed implementation milestone, update `docs/PROJECT_STATE.md` with:

```text
Current phase
Completed work
Work in progress
Known blockers
Next planned task
Important deviations/decisions
```

Keep it concise enough that a new developer or AI agent can understand the repository state quickly.

---

## 32. Scope Control

Do not add unplanned major features during the core implementation.

Initial scope does not require:
- IDE extensions,
- autonomous bug fixing,
- source-code execution,
- arbitrary private Git providers,
- collaborative editing,
- one universal cross-language model,
- automatic source rewriting,
- fabricated TypeScript predictions.

These belong in future scope unless the roadmap is explicitly changed.

---

## 33. No Premature Future-Phase Scaffolding

Only create structure needed for the current phase or a direct dependency.

During Phase 1, do not create empty implementations for every future analyzer, model, recommendation engine, or explainability feature merely to make the repository look complete.

Create future directories/modules when their phase starts or when a current-phase interface genuinely requires them.

---

## 34. Phase 1 Rules

During **Phase 1 — Repository Bootstrap & Developer Environment**, focus on:

- repository structure,
- FastAPI backend skeleton,
- React + TypeScript + Vite frontend skeleton,
- Tailwind setup,
- PostgreSQL configuration,
- Redis configuration,
- Celery configuration,
- Docker Compose,
- environment configuration,
- `/health`,
- linting,
- type checking,
- tests,
- CI,
- setup documentation.

Do not implement fake defect-prediction endpoints.

Do not add random placeholder probabilities.

Do not begin full authentication, secure repository ingestion, analyzers, or production ML unless explicitly required to unblock Phase 1 foundations.

---

## 35. Phase 1 Target Structure

The repository should evolve toward:

```text
KageX/
├── .github/
│   └── workflows/
├── backend/
│   ├── app/
│   └── tests/
├── frontend/
│   └── src/
├── docs/
│   ├── DESIGN.md
│   ├── DESIGN_REFERENCE.md
│   ├── FINAL_IMPLEMENTATION_PLAN.md
│   ├── PROJECT_STATE.md
│   ├── TECHNICAL_DECISIONS.md
│   └── design.html
├── AGENT.md
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
└── Makefile
```

Do not create empty future directories merely to match a later architecture diagram.

---

## 36. Phase Completion Rule

A phase is complete only when:

1. planned functionality exists,
2. relevant tests exist,
3. tests pass,
4. lint passes,
5. type checking passes,
6. required builds pass,
7. documentation is updated,
8. previous completed functionality still works,
9. the Definition of Done in `docs/FINAL_IMPLEMENTATION_PLAN.md` is satisfied.

If a required item remains incomplete, report it explicitly.

---

## 37. Change Discipline

Before modifying code:

1. identify the current phase,
2. identify the smallest coherent task,
3. inspect existing implementation,
4. inspect relevant project documentation,
5. implement,
6. test,
7. update docs if necessary,
8. summarize what changed.

Avoid unrelated refactors.

Do not rewrite stable code unless the requested task requires it.

---

## 38. When a Request Conflicts with the Plan

Do not silently violate frozen decisions.

If a requested change conflicts with security, ML validity, architecture, supported language/model policy, or the roadmap, identify:

1. the requested change,
2. the conflicting rule,
3. the safest compliant alternative.

---

## 39. Agent Completion Format

After a coding task, report:

### Changed
What was implemented.

### Files
Important files created or modified.

### Verification
Commands actually run.

### Result
Which checks passed or failed.

### Remaining
Known limitation, blocker, or next task.

Do not claim tests/checks passed unless they were actually run.

---

## 40. Core Engineering Principle

The central KageX pipeline is:

```text
safe source input
-> language detection
-> static analysis
-> versioned metric schema
-> compatible validated model
-> honest prediction state
-> risk interpretation
-> explanation
-> recommendation
-> interactive UI
```

Every major implementation decision should strengthen this pipeline.

Correctness, reproducibility, security, explainability, and a strong interactive user experience have priority over adding extra features.

---

## 41. Final Pre-Phase-1 Instruction

At the start of Phase 1:

1. do not redesign Phase 0,
2. do not alter the agreed ML strategy,
3. use `docs/design.html` as the visual prototype reference,
4. preserve the documentation structure already present,
5. build the minimum reliable foundation first,
6. leave the repository runnable after every meaningful step,
7. update `docs/PROJECT_STATE.md` as Phase 1 progresses.

**Phase 0 is frozen. Phase 1 begins from this contract.**

## 42. Phase 1 Repository Commands and Conventions

- Python 3.14; use `uv sync --locked` in `backend` and the committed `uv.lock`.
- Node 24 recommended (22.12+ within major 22 also supported); use `npm ci` in `frontend`.
- Copy root `.env.example` to root `.env`; both native applications load that root configuration.
- Native API: `cd backend && uv run python -m app` (factory: `app.main:create_app`).
- Native frontend: `cd frontend && npm run dev`.
- Development stack: `docker compose up --build --wait`; stop with `docker compose down`.
- Backend checks: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`, `uv run pytest` from `backend`.
- Frontend checks: `npm run lint`, `npm run format:check`, `npm run typecheck`, `npm test`, `npm run build` from `frontend`.
- Root `make check` runs both check groups; `make install` installs locked dependencies.
- Migrations: `cd backend && uv run alembic upgrade head`; consult PROJECT_STATE.md for the current schema.
- `/health` is dependency-free liveness; `/ready` checks PostgreSQL/Redis; application routes use `/api/v1`.
- Tailwind theme and shared CSS primitives live in `frontend/src/styles/index.css`.
- Keep frontend API requests in `frontend/src/services/api.ts`. Preserve unavailable states and response validation.
- Add future models to shared metadata and Alembic imports when their phase begins. Do not add domain tables to the Phase 1 baseline.
- CI configuration exists, but formal completion requires an observed green hosted run; consult PROJECT_STATE.md for actual verification.

## 43. Phase 2 Operational Rules

- Current domains are User, AuthSession, and Project. Source metadata is on Project; no analysis/ML tables or analyzer implementation belong to Phase 2.
- Cookie authentication requires trusted Origin plus `X-KageX-Request: 1` on unsafe requests. Never put session tokens into browser storage.
- All project endpoints, including both ingestion routes, use the central owned-project dependency. Preserve row locking on mutations.
- ZIP requests use raw ZIP bytes, not multipart. Never replace the bounded manual extractor with `extractall`, execution, imports, or repository dependency installation.
- Backend integration tests use real PostgreSQL, isolated schemas, and Alembic. Export `TEST_DATABASE_URL` when not using disposable Compose defaults.
- Run `npm run test:e2e` in frontend with the full stack running after changes to authentication or project workflows.
- Private source retention and crash-recovery limitations are documented in README and TD-011. Never expose the source volume as a static route.
- Phase 2 is complete; the project owner confirmed the delivered revision passed hosted CI. Phase 3 is ready to start when explicitly requested.

## 44. Phase 3 Operational Rules

- Phase 3 is complete/frozen; the owner confirmed hosted CI success. Phase 4A is complete/frozen; the owner confirmed hosted CI success. Phase 4B is ready to start when explicitly authorized.
- READY remains source preparation. AnalysisRun has separate QUEUED/RUNNING/COMPLETED/FAILED states; results are immutable after completion and retries create another run.
- Metric feature sets, semantics, tool versions and limitations are in docs/METRIC_SCHEMAS.md. Never silently change them or equate similarly named metrics across languages.
- Run source analyzers only in the worker using KageX-owned fixed tools/configuration. Never execute submitted source or install its dependencies.
- Native setup additionally needs trusted Java/Node analyzer tools: `npm ci --ignore-scripts --prefix app/analyzers/tools` and `uv run python app/analyzers/tools/install_ck.py` from backend. JDK 17+ is needed for the KageX wrapper only.
- Worker Docker image has trusted Java/Node runtimes, read-only source storage and bounded ephemeral scratch space. Rebuild worker after analyzer edits. Keep CK artifact readable by the non-root worker.
- All analysis endpoints must reuse project ownership/CSRF protection. PostgreSQL is authoritative; enforce active-run uniqueness and atomic publication.
- No prediction/risk/model behavior exists in Phase 3. TypeScript prediction remains MODEL_UNAVAILABLE. Hosted Phase 3 CI must pass before phase closure.

## 45. Phase 4A Operational Rules

- Only acquisition, provenance and descriptive audit are authorized. Do not train, transform features, construct labels/splits, select features, balance classes or implement inference. Do not start Phase 4B.
- Use `backend/app/dataset_sources.py`'s fixed approved catalog and `uv run python -m app.datasets` from backend. Read `docs/PHASE_4A_DATASET_AUDIT.md` and the five `data/manifests` records before resuming. Valid existing downloads must be verified and preserved; never regenerate a manifest just to accept changed upstream bytes.
- Benchmark repositories are untrusted data. No scripts, tests, dependency installs, hooks or binaries may run. Never deserialize untrusted pickle/joblib. Reuse secure archive extraction; keep raw/interim/processed data ignored.
- Unknown versions/licenses remain null. An acquired metadata repository is not a ready supervised dataset. PyTraceBugs acquisition was completed via Wayback Machine preservation of the official Huawei Cloud URL (verified payload and hashes); dataset/snippet licensing requires review for research/commercial distribution.
- Candidate features use actual Phase 3 contracts. Names alone do not establish compatibility. Keep TypeScript MODEL_UNAVAILABLE.
- Phase 4A hosted CI is owner-confirmed green for commit `7bbf452`. Phase 4A is complete and frozen; Phase 4B is ready to start when explicitly authorized.
