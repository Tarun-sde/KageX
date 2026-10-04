# KageX Project State

> Last updated: 2026-10-04. Frozen implementation plan version: 1.0.

## Current Status

```text
Phase 0 — Technical Research & Architecture Freeze: COMPLETE / FROZEN
Phase 1 — Repository Bootstrap & Developer Environment: COMPLETE / FROZEN
Phase 2 — Authentication, Projects & Secure Ingestion: COMPLETE / FROZEN
Phase 3 — Static Analysis Engine: COMPLETE / FROZEN
Phase 4A — Dataset Acquisition, Provenance & Audit: COMPLETE / FROZEN
Phase 4B — Feature Alignment, Metric Extraction & Ground Truth Formulation: READY TO START
```

The project owner confirmed Phase 1, Phase 2, Phase 3 and Phase 4A hosted CI success. The Phase 4A confirmation applies to the delivered implementation at repository head `7bbf452` (GitHub Actions workflows all green). Phase 4A is complete and frozen. No deployment or destructive Git operation was performed. The pre-existing `.gitignore` decision to allow project documentation remains preserved.

## Completed Phase 4A Handoff

- **COMPLETE:** Fixed approved-source acquisition CLI, five provenance/checksum manifests, inert extraction, descriptive profiles, all 37 Phase 3 feature candidates, license/scope findings, offline tests and relevant regression checks. PyTraceBugs dataset acquisition and recovery completed via authoritative Internet Archive capture (`20230808125225`) of the official Huawei Cloud URL; payload (1,960,844,036 bytes), RAR5 signature, archival CDX SHA-1, and SHA-256 confirmed. In-memory libarchive structural audit confirmed 47,172 entries, buggy/stable datasets, opaque pickle tables (`deserialized: false`), and inert AST text samples. Independent verification: PASS.
- **HOSTED CI:** PASS — all green in GitHub Actions for commit `7bbf452`. Phase 4A is complete and frozen.
- **BLOCKED:** None (external PyTraceBugs artifact resolved via authoritative archival preservation).
- **NON-BLOCKING REVIEW:** PyTraceBugs repository license is MIT (`LICENSE` pinned to commit `89a09db9add3ec174e3828b83e1792c6fc6ad5d2`). Dataset and underlying code snippet licensing remains `REQUIRES REVIEW`; this is not an acquisition/freeze blocker, but must remain visible for later research/commercial review.
- **PHASE 4B STATUS:** READY.

Measured inventory: Jureczko **2,494 class rows / 6 tables / 2 projects**; D'Ambros **5,371 class rows / 5 tables / 5 projects**; BugsInPy **501 bug instances / 17 projects**; BugsJS **453 bugs / 10 projects**; PyTraceBugs **47,172 archive entries / 47,169 regular files / 6 pickle tables / 47,160 Python snippet files**. BugsInPy contains **168 abbreviated revision pairs** and **one identical buggy/fixed pair with an empty patch**. No Python function labels or JavaScript file labels were manufactured. TypeScript remains `MODEL_UNAVAILABLE`.

All **54 downloaded artifacts** and **2,375 extracted files** are SHA-256 inventoried. Raw/interim/processed paths are ignored; five JSON manifests are tracked in Git. No dependencies, migrations, production analyzers, API/worker behavior, frontend or Docker files were changed. No benchmark code/tests/setup scripts ran, no benchmark dependencies were installed and no pickle was deserialized.

Local checks: **122 backend tests pass (17 dataset, 105 regression)**; Ruff lint/format and mypy pass on **51 Python files**. All five manifests/local inventories validate and fresh audit profiles match exactly. Hosted Phase 4A CI is **PASS** (green in GitHub Actions for commit `7bbf452`).

Full evidence, acquisition commands, and acceptance matrix: [PHASE_4A_DATASET_AUDIT.md](PHASE_4A_DATASET_AUDIT.md). Feature candidates and frozen analyzer versions: [PHASE_4A_FEATURE_REFERENCE.md](PHASE_4A_FEATURE_REFERENCE.md).

## Completed Phase 3 Handoff

Continued the existing partial Phase 3 implementation; valid work was preserved. Its implementation includes four real analyzers, versioned metric contracts, safe discovery/tool processes, PostgreSQL runs/entities, owner-scoped APIs, asynchronous Celery lifecycle, and frontend start/history/status/metrics/warnings. No Phase 4 code was part of that phase.

- **COMPLETE:** Core implementation, schema validation, analyzer correctness/security fixtures, persistence/ownership/idempotency/failure tests, frontend workflow, migration round trips, trusted worker image and CI setup.
- **HOSTED CI:** PASS, confirmed by the owner. Phase 3 is complete/frozen; no Phase 3 implementation work remains.

Phase 3 local backend verification: **105 tests pass**, including the 77 baseline tests, 18 analyzer/security cases and 10 lifecycle/API/migration cases; Ruff lint/format and mypy pass on 50 Python files. Frontend: **18 tests pass**, lint/format/types/build pass. Docker runs all four analyzers through real Celery/Redis/PostgreSQL; mixed fixtures persist nine entities. **Four browser tests pass**, covering successful mixed analysis and no-entity failure at 1440px and 390px. Detailed final gate evidence and all 71 acceptance criteria, including owner-confirmed hosted success, are in [PHASE_3_VERIFICATION.md](PHASE_3_VERIFICATION.md).

Important continuation notes: CK 0.7.0 has Java 11 grammar; its artifact must remain readable by UID 10001. Python MI is measured on normalized AST source. Java bindings can be incomplete without dependencies. Distinct language schemas and full tool/runtime version metadata must remain intact. See [METRIC_SCHEMAS.md](METRIC_SCHEMAS.md) and TD-013–015. Source preparation remains Phase 2 synchronous ingestion; static analysis is asynchronous. There is no ML, prediction, risk, SHAP or recommendation implementation.

Migration head is `f2de3d2ac9dd`. Compose supplies a worker-only Java/Node toolchain, read-only source mount, process/memory limits and ephemeral scratch. Normal scratch cleanup is automatic; hard crash recovery requires worker-container restart (or confirmed orphan removal with native workers stopped). Stale run deadlines are enforced lazily on reads/new-run/delete, not by a scheduler. The Compose development stack remains running. No commits, pushes or deployment have been performed.

## Completed Phase 2 Work

- PostgreSQL users, opaque hashed sessions, and owner-scoped projects; Alembic `6e605e1f5bed` after baseline `0001`.
- Registration, Argon2id password hashing, login/session rotation, current user, expiry/inactive-user checks, logout revocation, HttpOnly cookies, production Secure/host-only cookie policy, CSRF checks, restricted credentialed CORS, safe public schemas/errors.
- Project create/list/detail/rename/delete; owner filtering on every route, including uploads/imports; foreign/missing IDs share 404. Non-blocking row locks protect concurrent mutations.
- ZIP and public GitHub archive intake through one bounded inert extractor. UUID storage isolation, central-directory preflight, traversal/type/size/ratio/count/time protections, temporary cleanup, failure persistence, safe retries, and source deletion.
- Protected frontend sign-in/registration/project list/create/detail/source/rename/delete flows with real loading/error/empty/preparing states. READY explicitly means source prepared, never analysis complete.
- Private non-root Docker source volume, expanded environment documentation, PostgreSQL CI service/migration tests, and Playwright desktop/mobile Docker E2E job.
- README/API/security/retention instructions, AGENT operational guidance, and additive TD-009 through TD-012 decisions.

## Historical Phase 2 Verification

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
| Hosted Phase 2 GitHub Actions | **PASS** — confirmed by the project owner |

GNU Make is absent on this host; equivalent commands were executed directly. The verified Compose stack remains running at localhost:5173 / localhost:8000. Browser tests leave disposable test accounts; their projects are deleted. Final staging and deletion quarantine inspection found zero entries.

## Important Implementation Decisions

- Sessions are database-revocable opaque cookies, not JWTs. One-hour absolute expiry by default; no refresh endpoint or localStorage credentials.
- Source metadata lives on Project. Only User, AuthSession, Project were added; no speculative analysis/ML/job tables.
- Bounded preparation remains synchronous for Phase 2. Celery remains verified and available for the future asynchronous full-analysis pipeline; no ingestion Celery task exists.
- Source cannot be replaced after READY. Failed ingestion can be retried safely. Binary/nested archives are stored only as inert files.
- Native source root is ignored `.data/sources`; Docker root is private `/app/storage`. Prepared source is retained until project deletion in development; normal staging is context-managed and removed on success/failure.
- A crash between filesystem and DB operations can require offline reconciliation. Production retention/garbage collection, authentication throttling and quotas remain deployment hardening work. See TD-011 and README for the actual limitations and recovery approach.
- Review corrected duplicate generated enum constraints, malformed GitHub URL handling, disconnected/failed upload state, and ZIP offset ambiguity before final verification.

## Next Task

Phase 4A is COMPLETE / FROZEN with hosted CI confirmed green. Phase 4B (Feature Alignment, Metric Extraction & Ground Truth Formulation) is READY to start when explicitly authorized. Do not start Phase 4B until authorized. Preserve ownership, session, ingestion, storage, analyzer schemas, dataset manifests, and no-source-execution contracts.

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

Phase 1 authorized Phase 2. The completed Phase 2 implementation and verification are recorded at the top of this document.
