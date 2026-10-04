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
