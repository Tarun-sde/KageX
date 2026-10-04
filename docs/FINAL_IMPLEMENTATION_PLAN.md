# KageX — Final Implementation Plan

> **Project:** KageX — AI-Powered Software Defect Prediction & Code Risk Analysis  
> **Tagline:** Detect the unseen.  
> **Document status:** Final implementation baseline  
> **Phase 0 status:** COMPLETE / FROZEN  
> **Primary goal:** Build a secure, interactive web application that statically analyzes source code, extracts language-specific software metrics, predicts defect risk where a validated model exists, explains predictions, and presents actionable code-risk insights.

---

## 1. Final Product Vision

KageX accepts a software project through:

1. ZIP upload, or
2. Public GitHub repository import.

Both inputs are converted into one common analysis pipeline.

The system will:

1. Safely ingest the project.
2. Detect supported programming languages.
3. Analyze source code **without executing it**.
4. Extract static software metrics.
5. Normalize metrics into language/schema-specific feature records.
6. Select the correct validated model for that language and schema.
7. Predict defect probability when a compatible model exists.
8. Convert probability into a human-readable risk level.
9. Explain important risk factors.
10. Generate rule-based inspection/refactoring recommendations.
11. Store analysis history and results.
12. Show results through an interactive React dashboard.
13. Support comparison and report/export features.

---

# 2. Frozen Technical Decisions

These decisions were completed during Phase 0 and must not be casually changed during implementation.

## 2.1 Architecture

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
- XGBoost where appropriate
- imbalanced-learn where justified
- SHAP for supported model explanations
- Joblib / native model artifacts

### Quality
- pytest
- FastAPI TestClient / httpx
- Ruff
- mypy
- ESLint
- TypeScript type checking
- Vitest / React Testing Library
- Playwright for critical end-to-end flows
- GitHub Actions

---

## 2.2 Language and Model Strategy

KageX does **not** use one universal model for every programming language.

Each language has its own metric schema and compatible model.

| Language | Analysis Level | Main Metric Tooling | ML Status |
|---|---|---|---|
| Java | Class | CK + LOC-related metrics | Supported |
| Python | Function | Radon + AST-derived metrics | Supported |
| JavaScript | File | ESLint / Esprima / ts-morph-derived metrics | Supported |
| TypeScript | File / static analysis | ts-morph | **MODEL_UNAVAILABLE** until a validated labeled dataset exists |

### Mandatory rule

If there is no validated model compatible with the detected language and metric schema, the API must return an explicit model-unavailable state.

**Never fabricate a prediction.**

---

## 2.3 Frozen Dataset / Validation Direction

### Java
- PROMISE / Jureczko-style defect datasets
- D'Ambros-style CK/class-level metrics where applicable
- Class-level prediction

### Python
- BugsInPy / validated Python defect sources
- Function-level static metrics
- Radon + AST feature extraction

### JavaScript
- BugsJS
- File-level static metrics

### TypeScript
- Static analysis is allowed
- Defect prediction remains unavailable until a defensible labeled TypeScript dataset/model is validated

### Evaluation rules
- Avoid train/test leakage
- Prefer chronological/version-aware splits when appropriate
- Use project-aware validation
- Perform cross-project validation where feasible
- Use stratification when valid
- Record:
  - PR-AUC
  - ROC-AUC
  - F1
  - MCC
  - Brier score
- Never tune on the final test set

---

# 3. High-Level System Flow

```text
User
  |
  v
React / TypeScript UI
  |
  v
FastAPI
  |
  +---- Authentication / Project API
  |
  +---- ZIP Upload or Public GitHub Import
            |
            v
      Secure Ingestion Layer
            |
            v
      Language Detection
            |
            v
      Analyzer Registry
        /     |      |       \
     Java   Python   JS      TS
       |       |      |       |
       v       v      v       v
   Metrics   Metrics Metrics Metrics
        \      |      |      /
         v     v      v     v
      Common Analysis Records
              |
              v
      Model Compatibility Check
          /              \
      compatible       unavailable
         |                 |
         v                 v
    ML Inference     MODEL_UNAVAILABLE
         |
         v
   Defect Probability
         |
         v
      Risk Engine
         |
         v
 SHAP / Explanation
         |
         v
 Recommendation Engine
         |
         v
 PostgreSQL + API Response
         |
         v
 Dashboard / History / Comparison / Export
```

---

# 4. Core Architectural Principles

1. **Static analysis only.** Never execute uploaded project code.
2. **One ingestion pipeline.** ZIP and GitHub inputs converge after ingestion.
3. **Analyzer registry.** Language analyzers plug into a common interface.
4. **Schema-aware inference.** A model can only consume the schema it was trained for.
5. **Language-aware models.** Never force data from one language into another language's model.
6. **Explicit unsupported states.** Unsupported is a valid product result.
7. **Backend owns inference.** The browser never performs trusted preprocessing or ML inference.
8. **Reproducibility.** Model metadata, feature schema, version, and metrics must be recorded.
9. **Security first.** Uploaded repositories are untrusted data.
10. **Build vertical slices.** Every phase should leave the system runnable.

---

# 5. Final Phase Roadmap

---

# Phase 0 — Technical Research & ML/Data Freeze

**Status: COMPLETE / FROZEN**

### Completed decisions
- Final system architecture chosen.
- Supported-language strategy chosen.
- Metric granularity chosen per language.
- Dataset direction chosen.
- Separate-model strategy finalized.
- TypeScript ML restriction finalized.
- Leakage-safe evaluation rules finalized.
- Primary technology stack finalized.
- Static-only analysis rule finalized.

### Exit condition
Phase 0 must not be reopened during ordinary coding unless implementation proves a frozen assumption technically impossible.

---

# Phase 1 — Repository Bootstrap & Developer Environment

## Goal

Create a production-shaped repository that every later phase can safely build on.

## Deliverables

### Root
- `README.md`
- `AGENT.md`
- `.gitignore`
- `.env.example`
- `docker-compose.yml`
- `Makefile` or documented command equivalents
- `docs/`
- `.github/workflows/`

### Backend
Create a FastAPI application skeleton with:
- settings/configuration
- API router structure
- database configuration
- Redis configuration
- Celery application
- health endpoint
- test structure
- lint/type-check configuration

### Frontend
Create:
- React + TypeScript + Vite application
- Tailwind configuration
- routing skeleton
- app layout
- API client skeleton
- test configuration

### Infrastructure
Docker Compose services:
- backend
- frontend where useful for development
- PostgreSQL
- Redis
- Celery worker

### Required endpoint

```http
GET /health
```

Expected purpose:
- prove API is running
- optionally expose safe dependency status
- never expose secrets

## Definition of Done

- Fresh clone setup is documented.
- Frontend starts.
- FastAPI starts.
- `/health` succeeds.
- PostgreSQL is reachable.
- Redis is reachable.
- Celery worker starts.
- Backend lint passes.
- Backend type checking passes.
- Backend tests pass.
- Frontend lint passes.
- Frontend type checking passes.
- Frontend tests pass.
- Frontend production build passes.
- CI is green.
- No real secrets are committed.

### Canonical checks

```bash
ruff check .
mypy .
pytest

npm run lint
npm run typecheck
npm test
npm run build
```

---

# Phase 2 — Authentication, Projects & Secure Ingestion

## Goal

Allow a real user to create an analysis project and securely submit source code.

## Backend Tasks

### Authentication
Implement:
- user model
- password hashing
- login
- logout / token invalidation strategy
- current-user endpoint
- authorization checks

### Security requirement
Do not store long-lived authentication secrets in browser `localStorage`.

### Project lifecycle
Implement entities such as:
- User
- Project
- RepositorySource
- AnalysisRun
- AnalysisStatus

### Input methods
Support:
1. ZIP upload
2. Public GitHub URL

### Secure ZIP handling
Protect against:
- Zip Slip / path traversal
- decompression bombs
- oversized archives
- excessive file count
- unsupported binary content
- dangerous filenames

### GitHub ingestion
For the initial version:
- public repositories only
- validate host and URL
- enforce clone/download limits
- use temporary isolated workspace
- do not execute repository scripts/hooks

### Workspace lifecycle
- create per-analysis temporary workspace
- enforce size/time limits
- remove temporary source after analysis according to retention policy

## Frontend Tasks
- sign in / sign up screens
- dashboard shell
- create-project flow
- upload ZIP
- paste GitHub URL
- upload/import progress states
- friendly validation errors

## Definition of Done
A logged-in user can create a project and safely submit a supported source repository for analysis.

---

# Phase 3 — Static Analysis Engine

## Goal

Build the analyzer registry and produce trustworthy metrics without ML.

## Common analyzer contract

Each analyzer should provide a predictable interface conceptually similar to:

```python
class Analyzer:
    language: str
    schema_version: str

    def supports(self, path: Path) -> bool:
        ...

    def analyze(self, workspace: Path) -> list[MetricRecord]:
        ...
```

## Common metric record

Each record should include at minimum:

- analysis run ID
- language
- component type
- component identifier
- relative path
- metric schema version
- extracted metrics
- analyzer version
- warnings

---

## Java analyzer
Target:
- class-level records
- CK metrics
- LOC-related metrics

Candidate metrics include:
- WMC
- DIT
- NOC
- CBO
- RFC
- LCOM
- LOC

---

## Python analyzer
Target:
- function-level records

Use Radon + AST-derived features such as:
- LOC
- cyclomatic complexity
- Halstead measures
- maintainability-related values where appropriate
- parameter count
- branch/control-flow counts
- import/dependency counts where defined
- other frozen schema features

---

## JavaScript analyzer
Target:
- file-level records

Possible frozen-schema features:
- LOC
- cyclomatic complexity
- function count
- import count
- dependency indicators
- syntax/tree counts required by the trained model

---

## TypeScript analyzer
Target:
- static metrics using ts-morph
- result records available in UI
- prediction state must remain `MODEL_UNAVAILABLE`

---

## Mixed-language repositories
- detect each supported language
- analyze each using its own analyzer
- keep component granularity intact
- never merge incompatible feature schemas into one model input

## Definition of Done
Real repositories produce versioned static metric records for every supported analyzer, with tests using deterministic fixture repositories.

---

# Phase 4 — Dataset Pipeline & Model Training

## Goal

Create reproducible training pipelines and versioned model artifacts.

## Per-language pipeline

For every ML-supported language:

1. Load validated labeled dataset.
2. Validate schema.
3. Clean invalid rows.
4. Define features/target.
5. Split data using frozen leakage-safe rules.
6. Fit preprocessing using training data only.
7. Train baseline model.
8. Train candidate advanced models.
9. Evaluate.
10. Calibrate if justified.
11. Select model using documented criteria.
12. Save complete inference artifact.
13. Save metadata.

## Candidate models

At minimum evaluate appropriate subsets of:
- Logistic Regression
- Random Forest
- XGBoost

Do not choose a model only because its accuracy is highest.

Class imbalance and probability quality matter.

## Model artifact metadata

Each artifact must record:
- language
- analysis/component level
- metric schema version
- feature names and order
- preprocessing version
- training dataset/version
- model algorithm
- training timestamp
- validation metrics
- classification threshold/risk policy version
- software dependency versions where practical

## Required tests
- schema compatibility
- deterministic preprocessing
- expected feature ordering
- model load
- inference shape
- missing/invalid feature handling

## Definition of Done
Java, Python, and JavaScript each have a reproducible validated model artifact compatible with the production metric schema, or are explicitly marked unavailable if validation fails.

---

# Phase 5 — Prediction, Risk & Recommendation Engine

## Goal

Connect static metric records to safe model inference.

## Model registry

Create a registry keyed by values such as:

```text
(language, component_type, metric_schema_version)
```

Example behavior:

```text
Java + class + java_ck_v1 -> Java model
Python + function + python_static_v1 -> Python model
JavaScript + file + js_static_v1 -> JS model
TypeScript + ts_static_v1 -> MODEL_UNAVAILABLE
```

## Prediction output

A prediction record should include:
- component
- language
- model version
- defect probability
- risk level
- threshold/risk policy version
- explanation availability
- warnings

## Risk levels

Expose understandable labels such as:
- LOW
- MEDIUM
- HIGH
- CRITICAL

Thresholds must be versioned and evidence-based rather than arbitrary UI constants.

## Recommendation engine

Start with transparent deterministic rules.

Examples:
- very high complexity -> reduce branching / split responsibility
- high coupling -> inspect dependencies and module boundaries
- oversized component -> decompose
- low cohesion -> inspect responsibility separation

Recommendations must be phrased as inspection/refactoring guidance, **not claims that a specific bug definitely exists**.

## Definition of Done
Supported components receive real model-backed probabilities and risk labels; unsupported combinations receive explicit model-unavailable results.

---

# Phase 6 — Explainability & Analysis Orchestration

## Goal

Make predictions understandable and run full analyses asynchronously.

## Celery workflow

Example states:

```text
QUEUED
INGESTING
DETECTING_LANGUAGES
ANALYZING
PREDICTING
EXPLAINING
COMPLETED
FAILED
```

## Explainability

For compatible models:
- compute SHAP-based feature contributions where technically appropriate
- store top positive/negative factors
- map raw features to human-readable labels
- provide concise explanation summaries

Example:

```text
High cyclomatic complexity and coupling increased predicted defect risk,
while smaller method count reduced it.
```

## Failure handling
- one file/analyzer failure should not silently invalidate the entire run
- preserve warnings
- store safe user-facing failure reasons
- keep internal stack traces out of normal API responses

## Definition of Done
A submitted repository can run through the complete asynchronous analysis pipeline and return component-level results with explanations where available.

---

# Phase 7 — Full Interactive Frontend

## Goal

Turn the backend into a project that teachers/users can interact with directly.

## Main screens

### 1. Landing / Authentication
- project identity
- login/signup

### 2. Dashboard
- previous analyses
- project cards
- latest risk summary
- new-analysis action

### 3. New Analysis
- ZIP upload
- GitHub URL
- validation
- progress

### 4. Analysis Overview
Show:
- detected languages
- files/components analyzed
- model availability
- overall risk distribution
- warning count

### 5. Component Risk Table
Columns may include:
- component
- file
- language
- probability
- risk level
- important metrics

Features:
- sort
- filter
- search
- risk/language filters

### 6. Component Detail
Show:
- metrics
- predicted probability
- risk level
- explanation
- top contributing factors
- recommendations

### 7. Visualizations
Use Recharts for:
- risk distribution
- metric distribution
- highest-risk components
- comparison views

### 8. History / Comparison
- previous runs
- compare compatible analyses
- highlight risk changes

## Frontend rule
The UI visualizes backend truth. It must not invent predictions, alter model outputs, or reimplement trusted ML preprocessing.

## Definition of Done
A non-technical evaluator can upload/import a project, follow progress, understand the result, inspect risky components, and view recommendations without using API tools.

---

# Phase 8 — Integration, Security, Testing & Hardening

## Goal

Make the entire system reliable enough for demonstration and evaluation.

## Backend tests
- unit tests
- analyzer fixture tests
- model registry tests
- preprocessing/model compatibility tests
- authentication tests
- authorization tests
- upload validation tests
- API integration tests
- task/workflow tests

## Frontend tests
- component tests
- form validation
- API-state tests
- loading/error/empty states
- critical interaction tests

## End-to-end tests
At least:
1. authenticate
2. create project
3. submit sample repository
4. observe progress
5. receive analysis
6. open risky component
7. view explanation/recommendation

## Security hardening
Review:
- archive traversal
- file-size limits
- request-size limits
- repository download limits
- temporary file cleanup
- authorization
- CORS
- secret handling
- dependency vulnerabilities
- user-controlled paths
- HTML/script injection in displayed source metadata
- logging of secrets/source

## Performance
Measure:
- ingestion time
- static analysis time
- inference time
- explanation time
- total analysis time

Optimize only after measuring.

## Definition of Done
CI is green, critical user flows pass, known high-risk security issues are resolved, and the demo workflow is stable.

---

# Phase 9 — Feature Freeze, Polish & Final Release

## Goal

Stop adding architecture-changing features and prepare the academic/demo release.

## Tasks

### Product polish
- fix high-priority bugs
- improve empty/error states
- responsive layout
- loading/progress clarity
- accessibility pass

### Documentation
Finalize:
- README
- architecture documentation
- API overview
- local setup
- environment variables
- model/dataset documentation
- security limitations
- supported languages
- TypeScript model-unavailable explanation
- test instructions

### Academic material
Prepare:
- system architecture diagram
- data-flow diagram
- ML methodology
- metrics explanation
- validation results
- screenshots
- limitations
- future scope
- viva questions
- demo script

### Demo repositories
Keep small deterministic samples for:
- low-risk result
- high-risk result
- mixed-language project
- TypeScript static-analysis-only result
- malformed/unsupported input handling

### Release
- version tag
- production-like build
- frozen model artifacts
- reproducible demo instructions

## Definition of Done
A fresh environment can run KageX from documented instructions and complete the planned demonstration successfully.

---

# 6. Suggested Repository Structure

```text
kagex/
├── AGENT.md
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── docs/
│   ├── architecture/
│   ├── decisions/
│   ├── ml/
│   └── api/
│
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── tasks/
│   │   ├── ingestion/
│   │   ├── analyzers/
│   │   │   ├── base.py
│   │   │   ├── registry.py
│   │   │   ├── java/
│   │   │   ├── python/
│   │   │   ├── javascript/
│   │   │   └── typescript/
│   │   ├── ml/
│   │   │   ├── registry.py
│   │   │   ├── preprocessing/
│   │   │   ├── inference/
│   │   │   └── explainability/
│   │   └── recommendations/
│   └── tests/
│
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── types/
│   │   └── utils/
│   └── tests/
│
├── ml/
│   ├── datasets/
│   │   └── README.md
│   ├── pipelines/
│   │   ├── java/
│   │   ├── python/
│   │   └── javascript/
│   ├── artifacts/
│   └── reports/
│
├── fixtures/
│   └── repositories/
│
└── scripts/
```

Large datasets and generated model artifacts should not be blindly committed to Git. Use documented artifact handling/versioning.

---

# 7. Core Data Concepts

A practical initial domain model can include:

## User
Owns projects and analyses.

## Project
Logical software project within KageX.

## RepositorySource
Stores source type and safe metadata.

## AnalysisRun
Tracks one complete execution of the pipeline.

## ComponentMetric
Stores extracted static metrics.

## Prediction
Stores probability, risk level, model version, and compatibility state.

## Explanation
Stores explanation metadata/top contributing features.

## Recommendation
Stores rule-based guidance attached to a component.

---

# 8. API Direction

The exact URLs may evolve, but responsibilities should remain stable.

```text
GET    /health

POST   /auth/register
POST   /auth/login
GET    /auth/me

GET    /projects
POST   /projects
GET    /projects/{project_id}

POST   /projects/{project_id}/analyses/upload
POST   /projects/{project_id}/analyses/github

GET    /analyses/{analysis_id}
GET    /analyses/{analysis_id}/status
GET    /analyses/{analysis_id}/components
GET    /analyses/{analysis_id}/components/{component_id}

GET    /projects/{project_id}/history
```

Every project/analysis endpoint must enforce ownership/authorization.

---

# 9. Status and Compatibility Contract

Do not overload `null` to mean everything.

Use explicit states.

Example model status:

```json
{
  "language": "typescript",
  "prediction_status": "MODEL_UNAVAILABLE",
  "reason": "No validated compatible TypeScript defect model is available."
}
```

Possible prediction states:

```text
PREDICTED
MODEL_UNAVAILABLE
ANALYSIS_UNAVAILABLE
FAILED
```

Possible analysis states:

```text
QUEUED
RUNNING
COMPLETED
COMPLETED_WITH_WARNINGS
FAILED
```

---

# 10. Security Rules

KageX processes untrusted code.

Therefore:

- never execute submitted source code
- never run package install scripts from submitted projects
- never trust archive paths
- never trust filenames
- never trust repository metadata
- enforce archive/repository limits
- keep workspaces outside served directories
- do not expose filesystem paths
- remove temporary workspaces
- do not leak environment secrets
- do not log passwords/tokens
- sanitize user-controlled display values
- authorize every user-owned resource
- use parameterized ORM/database operations
- keep dependencies patched

---

# 11. ML Integrity Rules

1. Never fabricate a model result.
2. Never silently substitute one language model for another.
3. Never reorder features implicitly.
4. Never train preprocessing on final test data.
5. Never report training metrics as final validation.
6. Never call a probability a certainty.
7. Always keep schema/model versions.
8. Preserve reproducibility metadata.
9. Distinguish static-analysis findings from ML predictions.
10. TypeScript remains `MODEL_UNAVAILABLE` until validation is genuinely complete.

---

# 12. Team Development Split

The project can continue with the established two-developer split.

## Developer A — Analysis / ML / Data
Primary responsibility:
- datasets
- feature definitions
- analyzers where metric knowledge is required
- training pipelines
- model evaluation
- model artifacts
- SHAP/explainability validation
- ML documentation

## Developer B — Application / Backend / Frontend / Integration
Primary responsibility:
- repository bootstrap
- FastAPI
- PostgreSQL
- Redis/Celery
- authentication
- secure ingestion
- frontend
- API integration
- deployment/dev environment
- application tests

## Shared responsibility
Both developers:
- agree on schemas/contracts
- review integration code
- maintain tests
- update docs
- integrate at least once each week
- keep `main` runnable

---

# 13. Weekly Execution Discipline

At the beginning of each phase:

1. Read this implementation plan.
2. Read `AGENT.md`.
3. Define the phase checklist.
4. Work only on the current phase plus required blockers.
5. Add tests alongside implementation.
6. Update documentation for new configuration/contracts.
7. Run the canonical verification commands.
8. Record unresolved issues before moving forward.

Do not start the next phase merely because some code exists.

Move forward only when the current phase's definition of done is satisfied or an explicit exception is documented.

---

# 14. Scope Control

## Required for the final project
- interactive web application
- authenticated project workflow
- ZIP and public GitHub ingestion
- Java analysis + compatible ML
- Python analysis + compatible ML
- JavaScript analysis + compatible ML
- TypeScript static analysis with honest model-unavailable state
- risk scoring
- explanations where supported
- recommendations
- history
- useful dashboard/visualizations
- testing
- documentation

## Not required for the initial final-year implementation
- automatic source-code modification
- autonomous bug fixing
- executing user test suites
- arbitrary private Git provider integrations
- IDE extension
- real-time collaborative editing
- one universal cross-language model
- fabricated TypeScript predictions

These are future-scope candidates, not reasons to destabilize the main implementation.

---

# 15. Final Success Criteria

KageX is considered successfully implemented when a user can:

1. create an account
2. create a project
3. upload a ZIP or import a public GitHub repository
4. receive safe static analysis without project execution
5. see detected languages
6. view component-level software metrics
7. receive real defect-risk predictions for compatible Java/Python/JavaScript components
8. see an explicit `MODEL_UNAVAILABLE` result where prediction is unsupported
9. understand why a supported component was considered risky
10. receive actionable inspection/refactoring guidance
11. revisit previous analyses
12. compare compatible results
13. use the application through a polished interactive frontend

At the engineering level:

- tests pass
- lint passes
- type checking passes
- frontend build passes
- CI is green
- no real secrets are committed
- frozen model/data rules are respected
- the system is reproducible from documented setup instructions

---

# 16. Immediate Next Step

Start **Phase 1 — Repository Bootstrap & Developer Environment**.

Do not build fake prediction endpoints or placeholder ML values during Phase 1.

The purpose of Phase 1 is to create the reliable foundation required for every later phase.
