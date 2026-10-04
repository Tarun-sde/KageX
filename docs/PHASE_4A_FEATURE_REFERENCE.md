# Phase 4A feature candidates

This is preparation for a later, explicitly authorized Phase 4B. No feature is
validated as compatible. No features, labels, transforms or splits were constructed.
The exact production definitions remain in [METRIC_SCHEMAS.md](METRIC_SCHEMAS.md)
and `backend/app/analyzers/contracts.py`; model feature ordering is not defined here.

## Java: `java_class_v1`, class entities

Production: CK 0.7.0, bundled JDT Java 11 grammar; worker Java 17. Exact runtime
versions are persisted with metrics. Submitted dependencies are never resolved.
The acquired D'Ambros description identifies inFusion models; that is not evidence
of equivalence to the production CK tool. Jureczko column names alone prove nothing
about compatible tool versions or binding behavior.

| Production feature | PROMISE/Jureczko candidate | D'Ambros candidate | Status / review needed |
|---|---|---|---|
| `wmc` | `wmc` | `wmc` | REQUIRES_DEFINITION_REVIEW — complexity definition and method aggregation |
| `dit` | `dit` | `dit` | REQUIRES_DEFINITION_REVIEW — hierarchy roots, unavailable bindings |
| `noc` | `noc` | `noc` | REQUIRES_DEFINITION_REVIEW — children within which analysis boundary |
| `cbo` | `cbo` | `cbo` | REQUIRES_DEFINITION_REVIEW — coupling inclusion and binding resolution |
| `rfc` | `rfc` | `rfc` | REQUIRES_DEFINITION_REVIEW — method/call resolution and response set |
| `lcom` | `lcom` (not `lcom3`) | `lcom` | REQUIRES_DEFINITION_REVIEW — exact cohesion variant |
| `loc` | `loc` | `numberOfLinesOfCode` | REQUIRES_DEFINITION_REVIEW — class LOC, comment/blank/nested-type treatment |
| `num_functions` | NO_CANDIDATE for all methods; `npm` counts public methods | `numberOfMethods` | REQUIRES_DEFINITION_REVIEW for D'Ambros — declared/inherited/constructor treatment |

Production `num_functions` is CK method count. Public-method count must not be
silently substituted. Inheritance-related columns are not interchangeable. No
missing feature may be filled with zero to force inference. Dataset defect-count
columns are labels, not predictors; no binary target is created in this phase.

## Python: `python_function_v1`, function/method entities

Production: Radon 6.0.1 and Python 3.14 AST/tokenize; verified native 3.14.7 and
Docker 3.14.8. Each row below is **DATASET_DERIVED**, meaning future static extraction
would be necessary, not that extraction or label derivation has happened. BugsInPy
has metadata/patches, not full source revisions in this acquisition; PyTraceBugs'
full source artifact is unavailable. No existing metric column is established.

| Production feature | Required future evidence |
|---|---|
| `loc` | Original function physical span; preserve comments/blank lines |
| `sloc` | Radon raw source lines in that span |
| `cyclomatic_complexity` | Radon root function definition; nested closures separate |
| `halstead_volume` | Radon `h_visit_ast(function).total` |
| `halstead_difficulty` | Same exact subtree and Radon semantics |
| `halstead_effort` | Same exact subtree and Radon semantics |
| `maintainability_index` | `mi_visit(ast.unparse(function), multi=True)`; normalized source |
| `comment_density` | `(comments + multi) / loc` on original span; multiline strings included |
| `parameter_count` | All argument kinds, including `self`/`cls`, varargs and kwargs |
| `branch_count` | `If`, `IfExp`, `Match`; not match-arm count |
| `loop_count` | `For`, `AsyncFor`, `While`; exclude comprehensions |
| `return_count` | Function subtree `Return` nodes |
| `num_functions` | Nested sync/async definitions, excluding root |
| `num_classes` | Class definitions within function subtree |
| `import_count` | Import statements inside function subtree, not module imports |

Decorators are outside the function span; nested subtree overlap is deliberate.
Upstream snippets with comments/docstrings removed cannot silently replace original
source for raw metrics. Python 3.14 syntax acceptance of historical code must be
checked later without importing or executing it. Bug-fix localization and negative
sample policy are separate unresolved supervision questions.

## JavaScript: `javascript_file_v1`, file entities

Production: ESLint 10.12.0, ts-morph 28.0.0, TypeScript parser 6.0.2, Docker Node
24.14.0; fixed ESLint ECMAScript 2025/classic-complexity configuration. All eight
features below are **DATASET_DERIVED** from future acquired source files. BugsJS
test/coverage tables are not production static file metrics.

| Production feature | Required future evidence |
|---|---|
| `loc` | Original physical file lines, excluding final empty newline split |
| `num_functions` | AST function-like nodes with bodies, including arrows/accessors |
| `num_classes` | Class declarations and expressions |
| `import_count` | Exact import/export/require/dynamic-import syntax coverage |
| `coupling` | Distinct literal dependency specifiers, no resolution |
| `cyclomatic_complexity` | Sum of ESLint function/initializer/static-block units |
| `max_function_complexity` | Maximum over those units, zero when none |
| `complexity_units` | ESLint measured units, not a function-count alias |

BugsJS `Number of lines` and `Number of functions` are
**REQUIRES_DEFINITION_REVIEW** as descriptive coverage-table fields, not candidate
compatible file columns. Their granularity and measurement provenance differ.
No repository ESLint config, project plugins, tests or package scripts may run.

## TypeScript: `typescript_file_v1`, file entities

Production: ts-morph 28.0.0 / TypeScript 6.0.2; fixed in-memory parser with no
resolution or emit. Each feature is **NO_CANDIDATE**: `loc`, `num_functions`,
`num_classes`, `import_count`, `coupling`, `decision_count`. There is no approved
TypeScript defect dataset. Prediction remains **MODEL_UNAVAILABLE**. No replacement
dataset was searched for and no JavaScript model may be substituted.

All **37** production features are accounted for. No compatibility decision,
feature selection, model feature ordering or new schema is introduced.
