# KageX — Technical Decisions

Status: BASELINE FROZEN (Phase 0 Complete)  
Project: KageX — AI-Powered Software Defect Prediction & Code Risk Analysis  
Tagline: Detect the unseen.  

This document records accepted technical, architectural, and ML research decisions.

---

## Executive Summary: Decision Matrix

| Language | Dataset (License) | Granularity | Features (extracted statically) | Model Status |
|---|---|---|---|---|
| **Java** | PROMISE/Eclipse (class-level, EPL) | Class (Java class) | CK metrics (WMC, CBO, RFC, LCOM, DIT, NOC) + LOC | **VALID** (class model) |
| **Python** | BugsInPy (493 bugs, MIT/Apache) | Function/module | LOC, Cyclomatic Complexity, MI, Halstead metrics, func/class counts (Radon/AST) | **VALID** (function model) |
| **JavaScript** | BugsJS (453 bugs, MIT) | File/module | LOC, Cyclomatic Complexity, #functions, #classes (ESLint/AST) | **VALID** (file model) |
| **TypeScript** | – (no dataset) | File/module (TS code) | Same static metrics via ts-morph/ESLint | **MODEL_UNAVAILABLE** |

Each approved model must exactly match the dataset’s feature schema and preprocessing. Where no approved model exists (TypeScript), the system will report `MODEL_UNAVAILABLE` rather than guessing or fabricating predictions.

---

## TD-001: Separate Per-Language Models and Granularity

- **Decision**: Train independent defect-prediction models for each language ecosystem rather than a unified cross-language model.
- **Granularity**:
  - **Java**: Class-level (matches Jureczko PROMISE / D'Ambros 2010 labels and OO design).
  - **Python**: Function/method-level (matches BugsInPy localized defect repairs and PyTraceBugs snippets).
  - **JavaScript**: File/module-level (matches BugsJS module-level patches).
  - **TypeScript**: File/module-level. Statically analyzed via ts-morph/TypeScript AST, but **no ML model** (returns `MODEL_UNAVAILABLE`) until a dedicated labeled TS dataset is obtained.
- **Rationale**: Languages exhibit fundamentally different idioms, metric distributions, and AST semantics. Granularities align directly with where labels originate in established defect benchmarks.

---

## TD-002: Java Defect Dataset and Analyzer Compatibility

- **Dataset**: Jureczko PROMISE (2010) and D'Ambros et al. (2010) "Bug Prediction Dataset" (Eclipse JDT Core, PDE UI, Equinox, Lucene, Mylyn).
- **License**: EPL / Apache / permissive open-source.
- **Label**: Binarized post-release defect count (>0 defects = 1, otherwise 0).
- **Target Features**: CK metric suite (WMC, DIT, NOC, CBO, RFC, LCOM) + size/count measures (LOC, method count).
- **Analyzer**: [CK tool](https://github.com/mauricioaniche/ck) (Apache-2.0) + JavaParser.
- **Status**: Compatible. The CK suite produced by the analyzer maps directly to the PROMISE/D'Ambros training feature schema.

---

## TD-003: Python Defect Dataset and Analyzer Compatibility

- **Dataset**: BugsInPy (Widyasari et al., 2020/2024; 493 real bugs across 17 projects) and PyTraceBugs (APSEC 2021; function snippets).
- **License**: MIT / Apache-2.0.
- **Label**: Binary (function/method modified in bug-fix commit = 1, otherwise 0).
- **Target Features**: LOC, Cyclomatic Complexity (CC), Comment Density, Halstead Volume, Maintainability Index (MI), function and class counts.
- **Analyzer**: Radon (MIT) + Python stdlib `ast`.
- **Status**: Compatible. Fine-grained function-level extraction maps directly to localized bug commits.

---

## TD-004: JavaScript/TypeScript Dataset and Analyzer Strategy

- **Dataset**: BugsJS (Di Sorbo et al., 2020) across 10 Node.js projects (453 validated bugs, MIT license).
- **TypeScript Dataset**: *None currently available*.
- **Label (JS)**: Binary (file modified in bug-fix commit = 1, otherwise 0).
- **Target Features**: LOC, Cyclomatic Complexity per function/aggregated, function count, class count, comment density, import/coupling count (`require`/`import`).
- **Analyzer**: ESLint (complexity rules) + `ts-morph` / Esprima (AST counts, imports).
- **TypeScript Policy**: In accordance with `AGENT.md` (no fabricated predictions), TypeScript files receive full static metric extraction via `ts-morph`, but ML risk probability returns `MODEL_UNAVAILABLE` until a verified TS benchmark is introduced.

---

## TD-005: Common Feature Schema Baseline

A shared baseline feature schema is defined across analyzers:

| Feature | Unit | Java (CK/JavaParser) | Python (Radon/AST) | JS/TS (ESLint/ts-morph) |
|---|---|---|---|---|
| `loc` | Integer | Lines of code | Lines of code (Radon raw) | AST line count |
| `cyclomatic_complexity` | Integer | McCabe CC (CK / PMD) | McCabe CC (Radon cc) | ESLint complexity |
| `comment_density` | Float | Comment / Total lines | Comment / Total lines | Regex / AST comment ratio |
| `num_functions` | Integer | Method count | Function def count (`ast`) | Function count |
| `num_classes` | Integer | Class count | Class def count (`ast`) | Class declaration count |
| `inheritance_depth` | Integer | DIT | Class bases depth | Heritage clause depth (TS) / 0 |
| `coupling` | Integer | CBO | Distinct imports count | Distinct `import`/`require` count |

Language-specific metrics (Halstead, MI for Python; RFC, LCOM for Java) will be retained in language-specific schema extensions (`schema-java-v1`, `schema-python-v1`, `schema-javascript-v1`).

---

## TD-006: Leakage-Safe Evaluation Protocol

To ensure rigorous, defensible defect prediction:
- **Time/Version Splitting**: Chronological partitioning where version history exists (train on older releases, test on newer releases). Prevents future bug fixes leaking into features.
- **Cross-Project Splitting**: Leave-one-project-out (train on $N-1$ projects, test on remaining held-out project) to evaluate generalization.
- **Stratified Sampling**: Account for severe class imbalance without leaking test distribution into training preprocessing.
- **Evaluation Metrics**: Precision, Recall, F1-score, PR-AUC, ROC-AUC, MCC, and Brier score (probability calibration).
- **Strict Boundary**: Zero overlap of source code artifacts or AST snippets between train and test sets.

---

## TD-007: Phase 0 Exit and Phase 1 Authorization

- **Phase 0 Status**: BASELINE FROZEN.
  - Java: PROMISE/D'Ambros, class-level, CK + LOC (GO).
  - Python: BugsInPy/PyTraceBugs, function-level, Radon + AST (GO).
  - JavaScript: BugsJS, file-level, ESLint + ts-morph (GO).
  - TypeScript: ts-morph static analysis (GO), ML inference = `MODEL_UNAVAILABLE` (GO).
  - Evaluation protocol defined (TD-006).
- **Phase 1 Authorization**: Implementation of project skeleton, database, worker, backend, and frontend is fully approved.
- **Phase 4 (Model Training) Gate**: Models will train strictly against the schemas and protocols documented in TD-001 through TD-006.

---

## TD-008: Static-Analysis-Only Security Constraint (No Source Execution)

- **Untrusted Input Principle**: All user-submitted repositories (ZIP archives and cloned GitHub repositories) are untrusted data.
- **Execution Prohibition**: KageX must **NEVER execute, import, run tests, or trigger build lifecycle scripts** (e.g., `npm install`, `pip install`, `mvn compile`, `gradle build`, or git hooks) on user-uploaded or cloned code.
- **Safe Static Inspection**: All language analyzers must rely strictly on offline static AST parsing, lexical analysis, and metric calculation tools (e.g. Radon, Python `ast`, CK tool, ESLint, `ts-morph`) within isolated temporary workspaces.
- **Permanent Project Rule**: This security constraint applies to all phases and must never be relaxed for developer convenience.

## TD-009: Phase 2 First-Party Identity and Sessions (2026-10-04)

Use PostgreSQL User/AuthSession records and Argon2id via argon2-cffi. Password length is 12–128 characters; normalized lowercase email has a database unique constraint. The default Argon2id parameters are 64 MiB memory, three iterations, four lanes, with per-password salt and rehash support. Nonexistent login attempts perform dummy-hash verification.

Use 256-bit random opaque cookie sessions, stored only as SHA-256 digests with absolute expiry. Default lifetime is one hour; login rotates the presented session, logout deletes it, inactive users and expired sessions cannot authorize requests. There is no JWT, refresh token, OAuth provider, or signing secret. Production cookies are Secure/HttpOnly/SameSite=Lax/host-only under the `__Host-` prefix. Development cookies allow localhost HTTP. Unsafe requests require an exact trusted Origin and custom request header; CORS only admits configured origins. This is a same-site browser application, not a cross-site public authentication SDK.

References: [argon2-cffi usage](https://argon2-cffi.readthedocs.io/en/stable/howto.html), [OWASP CSRF guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html). Production authentication throttling, reset/verification emails, and account recovery are outside this local Phase 2 foundation.

## TD-010: Minimal Owned Project Lifecycle (2026-10-04)

Project contains owner UUID, name, ZIP_UPLOAD/GITHUB source type, CREATED/READY/FAILED status, canonical public repository URL if applicable, safe error code, actual source file/byte counts, and timestamps. User/Project/AuthSession are the only new tables. No empty RepositorySource, AnalysisRun, job, metrics, or prediction tables are added: source is immutable after successful preparation and no analysis exists yet.

Every project access filters both identifier and owner. Foreign and missing resources share 404; write requests lock the row with NOWAIT and report PROJECT_BUSY on concurrent writes. Name is the only editable field. Client ownership/status fields are forbidden. READY means source preparation succeeded, never that metrics or predictions exist. Phase 3 must introduce its own analysis-run lifecycle without reinterpreting READY.

## TD-011: Bounded Ingestion and Local Retention (2026-10-04)

ZIP uploads and public GitHub default-branch archive downloads use one inert extraction/storage pipeline. Compressed input defaults to 25 MiB, expanded total 100 MiB, per-file 10 MiB, 2000 entries, expansion ratio 100, and 30-second preparation deadline. GitHub also uses five-second network-operation timeouts; an in-progress network read may finish up to five seconds after the overall deadline. No automatic network retries or redirects occur. UI progress is a busy state, not an invented progress percentage.

This bounded Phase 2 preparation is synchronous; no Celery ingestion task or persisted job queue is needed. Celery/Redis remain verified for future asynchronous analysis. This does not change the frozen asynchronous full-analysis architecture. Row locks serialize ingestion/delete/retry. On normal rejection, FAILED and a safe error code persist and staging is removed. Retrying FAILED starts in fresh staging; READY source cannot be overwritten.

Raw ZIP bodies avoid multipart spooling before authorization. Central-directory counts and exact offsets are checked before allocating ZipInfo objects. Entry paths/types/sizes/ratios and actual extraction bytes/deadlines are checked. Only stored/deflated regular files and directories are accepted. ZIP64, split/self-extracting ZIPs, symlinks, special files, encryption, traversal, and conflicting paths are rejected. Nested archives and binary files remain inert bytes; no recursive extraction or binary analysis occurs. GitHub URLs must be exact HTTPS GitHub.com owner/repository URLs; download requests go only to fixed HTTPS codeload.github.com, with environment proxies and redirects disabled.

Storage uses isolated random staging directories and UUID project directories outside web/static roots. Completed files have mode 0600 under private project roots. Native default is ignored `.data/sources`; Docker uses non-root-owned private `source_data`. Normal temporary files are always context-managed. Prepared sources are retained until project deletion during local development. Deletion quarantines before DB commit, restores on rollback, and removes quarantine after commit. Cleanup IO failures are logged safely.

A database transaction cannot make filesystem operations crash-atomic. Abrupt process/host death may leave staging, published-but-uncommitted source, or deletion quarantine requiring offline reconciliation. Before production use, define retention/garbage collection, crash reconciliation, global admission limits and per-user quotas. Operator recovery: stop API writes, inspect project UUID/status records against private storage, restore quarantine for extant projects as appropriate, and remove only confirmed orphan staging/source/trash. Never expose raw source paths through the API or indiscriminately remove the source volume. Future analyzers must use isolated workspaces and apply a deliberate retention policy.

## TD-012: Phase 2 Verification Gates (2026-10-04)

Integration tests run PostgreSQL migrations in isolated schemas, never SQLite substitutes or shared-table truncation. Tests cover authentication, CSRF, ownership for all mutations/intake routes, concurrent row locks, storage rollback, malformed/hostile ZIPs, size/ratio/count/time limits, fixed-host GitHub intake, and failure retry. Playwright is now justified by real critical account/project flows and runs against the full Docker stack at desktop/mobile sizes. No submitted code is executed by tests or application ingestion.

The owner confirmed Phase 1 and Phase 2 hosted CI success. Phase 2 is complete and frozen; Phase 3 is ready to start when explicitly requested. All Phase 0 ML/data/security decisions remain frozen.

## TD-013: Phase 3 Static Metrics and Reproducibility (2026-10-04)

Phase 3 implements CK 0.7.0 class metrics, Radon 6.0.1 plus Python AST function metrics, ESLint 10.12.0 plus ts-morph 28.0.0 JavaScript file metrics, and ts-morph TypeScript file metrics. TypeScript parser 6.0.2 is locked transitively. [METRIC_SCHEMAS.md](METRIC_SCHEMAS.md) and the central contracts module define exact features and versioned schemas. Runtime versions are recorded per entity. No generic cross-language complexity vector, JavaParser duplicate implementation, predictions, training or model registry is added.

CK's bundled JDT accepts Java 11 syntax; unsupported syntax is a warning. CK is checksum-pinned and receives no submitted dependencies. Class binding limitations are explicit entity warnings. Python includes nested function entities and documents overlapping subtree metrics; MI uses normalized AST source to handle indentation and multiline strings safely. JS complexity uses only fixed ESLint configuration; TS structural decisions remain a distinct metric. Repository ESLint/tsconfig/package configuration cannot control tools. Dependencies are installed only from KageX's locks during setup/build.

## TD-014: Durable Analysis Runs and Bounded Workers (2026-10-04)

Add only AnalysisRun and AnalysisEntity. Foreign keys cascade project → runs → entities. A PostgreSQL partial unique index enforces one active run per project; identity uniqueness prevents duplicate entities. Owner-scoped APIs commit QUEUED before publishing its UUID. Worker advisory locking, late acknowledgement, original deadlines, and terminal no-ops protect duplicate deliveries. Results publish atomically. A failed enqueue persists a safe failure; no transactional outbox is added. If the API dies between commit and publish, reads/new-run/delete operations expire the stale run after its deadline. There is no periodic recovery service.

Existing immutable source is discovered under the server's UUID root and copied with no-follow regular-file reads into a private workspace. Commands are fixed arrays, environment is sanitized, and tool/CPU/output/memory/task limits apply. Linux parent-death protection kills orphan analyzers. Docker uses a non-root worker, read-only source volume, 2 GiB memory, 128 PIDs, and 512 MiB private tmpfs. Normal cleanup is automatic; hard-crash orphan scratch is discarded by worker-container restart. Native cleanup requires stopped workers and confirmed orphan directories. Operators must complete that recovery rather than retain scratch indefinitely.

Parse failures yield relative-path warnings; useful entities can complete with warnings. Tool failure, expiry, or no analyzable entities yields FAILED and no partial metric publication. Public APIs never expose source, raw tool output, stack traces or internal paths. READY continues to describe preparation only. Project deletion is blocked for active analysis; retries create another run. No additional progress state, percent-complete estimate, cancellation API, automatic retry loop, scheduler or service is required for Phase 3.

## TD-015: Phase 3 Verification Gate (2026-10-04)

Real fixture-based analyzers, PostgreSQL lifecycle/ownership/migration tests, frontend polling/error tests and browser flows through the real Docker Celery worker are required. CI installs only trusted analyzer dependencies and runs these checks. Local success does not replace a hosted run for the delivered revision. Phase 3 remains incomplete and Phase 4 not ready until hosted GitHub Actions is green.
