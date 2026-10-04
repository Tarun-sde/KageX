# KageX Project State

> Last updated: 2026-10-04. Frozen implementation plan version: 1.0.

## Current Status

```text
Phase 0 — Technical Research & Architecture Freeze: COMPLETE / FROZEN
Phase 1 — Repository Bootstrap & Developer Environment: COMPLETE / FROZEN
Phase 2 — Authentication, Projects & Secure Ingestion: INCOMPLETE — hosted CI verification pending
Phase 3 — Static Analysis Engine: NOT STARTED / NOT AUTHORIZED
```

The project owner confirmed Phase 1 hosted CI success. Phase 2 was continued from the current partial implementation, preserving valid work. All applicable local implementation/verification gates now pass; the updated workflow has not run successfully on hosted GitHub Actions for these uncommitted changes. No commit, push, deployment, or destructive Git operation was performed. The pre-existing `.gitignore` decision to allow project documentation remains preserved.

## Completed Phase 2 Work

- PostgreSQL users, opaque hashed sessions, and owner-scoped projects; Alembic `6e605e1f5bed` after baseline `0001`.
- Registration, Argon2id password hashing, login/session rotation, current user, expiry/inactive-user checks, logout revocation, HttpOnly cookies, production Secure/host-only cookie policy, CSRF checks, restricted credentialed CORS, safe public schemas/errors.
- Project create/list/detail/rename/delete; owner filtering on every route, including uploads/imports; foreign/missing IDs share 404. Non-blocking row locks protect concurrent mutations.
- ZIP and public GitHub archive intake through one bounded inert extractor. UUID storage isolation, central-directory preflight, traversal/type/size/ratio/count/time protections, temporary cleanup, failure persistence, safe retries, and source deletion.
- Protected frontend sign-in/registration/project list/create/detail/source/rename/delete flows with real loading/error/empty/preparing states. READY explicitly means source prepared, never analysis complete.
- Private non-root Docker source volume, expanded environment documentation, PostgreSQL CI service/migration tests, and Playwright desktop/mobile Docker E2E job.
- README/API/security/retention instructions, AGENT operational guidance, and additive TD-009 through TD-012 decisions.

## Verification Executed

Full evidence, security coverage, file inventory, and every acceptance criterion are in [PHASE_2_VERIFICATION.md](PHASE_2_VERIFICATION.md).

| Gate | Actual result |
|---|---|
| Locked dependency installation | PASS — `uv sync --locked`, `npm ci`; npm audit reports zero vulnerabilities |
| Ruff lint / format / mypy | PASS — 31 Python files |
| Backend pytest | PASS — **77 tests**, including all 9 Phase 1 tests |
| Frontend lint / format / TypeScript | PASS |
| Frontend Vitest | PASS — **14 tests**, including foundation regressions adapted to protected workspace |
| Frontend production build | PASS |
| Playwright against Docker | PASS — **2 tests**, complete account/project lifecycle at 1440px and 390px; no page errors/overflow |
| Docker config/build/startup | PASS — all five long-running services healthy, migrations exited 0 |
| `/health`, `/ready` and queued Celery result | PASS — PostgreSQL/Redis ready, `pong` through real broker/worker |
| Container Alembic schema check | PASS — no pending operations |
| Fresh PostgreSQL database in Docker | PASS — upgrade, schema check, downgrade to base, re-upgrade, schema check; disposable database removed |
| Isolated-schema integration tests | PASS — real migrations, independent transactions, ownership/locking/failure/retry checks |
| Live public GitHub import | PASS — octocat/Hello-World snapshot reached READY; verification project/source deleted |
| Native API/Vite startup | PASS — readiness at 8011, frontend at 5174; temporary native processes stopped |
| CI YAML parsing/structure | PASS — PyYAML parsing and job/step checks; reviewed service/command wiring |
| Source/credential audit and diff whitespace | PASS — no source execution/installation path, no probable secret-pattern matches, `.env`/`.data` ignored |
| Hosted Phase 2 GitHub Actions | **NOT TESTED** — remaining formal gate |

GNU Make is absent on this host; equivalent commands were executed directly. The verified Compose stack remains running at localhost:5173 / localhost:8000. Browser tests leave disposable test accounts; their projects are deleted. Final staging and deletion quarantine inspection found zero entries.

## Important Implementation Decisions

- Sessions are database-revocable opaque cookies, not JWTs. One-hour absolute expiry by default; no refresh endpoint or localStorage credentials.
- Source metadata lives on Project. Only User, AuthSession, Project were added; no speculative analysis/ML/job tables.
- Bounded preparation remains synchronous for Phase 2. Celery remains verified and available for the future asynchronous full-analysis pipeline; no ingestion Celery task exists.
- Source cannot be replaced after READY. Failed ingestion can be retried safely. Binary/nested archives are stored only as inert files.
- Native source root is ignored `.data/sources`; Docker root is private `/app/storage`. Prepared source is retained until project deletion in development; normal staging is context-managed and removed on success/failure.
- A crash between filesystem and DB operations can require offline reconciliation. Production retention/garbage collection, authentication throttling and quotas remain deployment hardening work. See TD-011 and README for the actual limitations and recovery approach.
- Review corrected duplicate generated enum constraints, malformed GitHub URL handling, disconnected/failed upload state, and ZIP offset ambiguity before final verification.

## Remaining Gate and Next Task

Obtain a green hosted run of the updated `.github/workflows/ci.yml` for the delivered Phase 2 revision, then record the actual run URL/result. **Phase 2 remains incomplete and Phase 3 is NOT READY.** Do not start analyzers or ML now.

Useful commands: `docker compose up --build --wait`; backend `uv run pytest`, `uv run alembic check`; frontend `npm run test:e2e` against the running full stack. README contains all checks and environment settings. Backend tests need real PostgreSQL and schema-creation privileges; export `TEST_DATABASE_URL` for non-default test credentials.

---

## Frozen Architectural Decisions

1. **Interactive Web Application**: KageX is an interactive web application, not a CLI or Jupyter notebook.
2. **Unified Post-Ingestion Pipeline**: ZIP upload and public GitHub import converge into a single downstream analysis pipeline.
3. **Static Analysis Only (Security Rule)**: Uploaded and cloned project source code is treated as untrusted input and is **NEVER executed**, imported, or built.
4. **Temporary Workspaces**: Raw source code is stored in isolated temporary workspaces and purged according to retention policy.
5. **Launch Ecosystems**: Java, Python, and JavaScript/TypeScript form the initial launch scope.
6. **Mixed-Language Repositories**: Analyzed per supported language; never collapsed into a single forced primary language.
7. **Analyzer Registry**: Analyzers plug into a common interface producing versioned metric records.
8. **Schema-Aware Inference**: Models are strictly matched to the exact language, component granularity, metric schema, and feature order they were trained on.
9. **Separate Per-Language Models**: Independent models per language ecosystem. A universal cross-language ML model is not used.
10. **No Fake ML Predictions**: If no validated model exists for a language or schema, the system returns `MODEL_UNAVAILABLE`. Probabilities and labels are never fabricated.
11. **TypeScript Limitation**: TypeScript receives static code-risk analysis via `ts-morph`, but ML defect prediction explicitly returns `MODEL_UNAVAILABLE` due to the lack of a verified labeled TypeScript benchmark.
12. **PostgreSQL as Primary Store**: Relational entities track users, projects, runs, metrics, predictions, explanations, and recommendations.
13. **Asynchronous Analysis**: Long-running ingestion, analysis, inference, and explanation jobs execute asynchronously via Celery and Redis.
14. **Authentication & Authorization**: Ownership is strictly enforced on all user-owned resources; secrets are never stored in browser `localStorage`.
15. **Evidence-Based Recommendations**: Guidance points to refactoring and inspection; it does not claim certainty that a bug exists.
16. **Explainability Boundaries**: SHAP values explain model feature contributions, never causal runtime defects.
17. **Model Governance**: Model versions, analyzer versions, and metric schemas are persisted with every analysis run for reproducibility.
18. **Evaluation Integrity**: Data leakage is prevented via chronological/version-aware and cross-project splitting. Evaluation uses PR-AUC, ROC-AUC, F1, MCC, and Brier score.
19. **Design Prototype Separation**: `docs/design.html` is a visual reference only; prototype logic/mock data must not be copied into production code.
20. **Documentation as Source of Truth**: All architectural and technical decisions are permanently recorded in `docs/TECHNICAL_DECISIONS.md`.

---

## Phase 0 Research Status (COMPLETE / FROZEN)

All Phase 0 research requirements are finalized in `docs/TECHNICAL_DECISIONS.md`:

| Decision ID | Area | Frozen Decision | Status |
|---|---|---|---|
| **TD-001** | Model Strategy | Separate per-language models; independent granularities | **FROZEN / GO** |
| **TD-002** | Java | PROMISE (Jureczko 2010) / D'Ambros 2010; class-level; CK metrics + LOC; CK tool analyzer | **FROZEN / GO** |
| **TD-003** | Python | BugsInPy / PyTraceBugs; function-level; LOC, CC, Halstead, MI, counts; Radon + AST analyzer | **FROZEN / GO** |
| **TD-004** | JavaScript | BugsJS; file-level; LOC, CC, counts, imports; ESLint + ts-morph / Esprima analyzer | **FROZEN / GO** |
| **TD-004** | TypeScript | Static metrics via ts-morph (GO); defect prediction = `MODEL_UNAVAILABLE` (no fake output) | **FROZEN / GO** |
| **TD-005** | Schema | Common normalized feature schema baseline with language-specific schema extensions | **FROZEN / GO** |
| **TD-006** | Evaluation | Leakage-safe protocol: temporal/version & cross-project splitting, stratification, PR-AUC, ROC-AUC, F1, MCC, Brier score | **FROZEN / GO** |
| **TD-007** | Phase Exit | Phase 0 baseline frozen; Phase 1 authorized | **FROZEN / GO** |
| **TD-008** | Security | Static-analysis only; untrusted input handling; source code execution strictly prohibited | **PERMANENT CONSTRAINT** |

---

## Phase 1 — Foundation / Repository Bootstrap

**Status:** COMPLETE / FROZEN

### Verification
- Backend tests: PASS
- Frontend tests: PASS
- Python lint/format/type checks: PASS
- Frontend lint/type/build checks: PASS
- Docker Compose validation: PASS
- PostgreSQL connectivity: PASS
- Redis connectivity: PASS
- Celery worker/task verification: PASS
- Hosted GitHub Actions CI: PASS

### Phase 1 Result
The KageX development foundation is complete and verified.

Implemented:
- React + TypeScript + Vite frontend
- Tailwind CSS design foundation
- FastAPI backend
- Typed environment configuration
- PostgreSQL + SQLAlchemy
- Alembic migrations
- Redis
- Celery
- Docker + Docker Compose
- Health/readiness endpoints
- Frontend/backend integration
- Testing and static analysis
- GitHub Actions CI

### Frozen Constraints Preserved
- Separate per-language ML models
- Java: class-level prediction
- Python: function-level prediction
- JavaScript: file-level prediction
- TypeScript defect prediction: MODEL_UNAVAILABLE
- Uploaded user code is never executed
- No fake ML predictions or model outputs

### Historical Phase 1 Handoff

Phase 1 authorized Phase 2. The current Phase 2 implementation and remaining hosted CI gate are recorded at the top of this document. The pasted continuation instructions have been incorporated into that current status and verification record.
