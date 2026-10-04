# Phase 3 static metric contracts

These are measured static properties, not predictions, vulnerabilities, defect labels, or risk scores. No model is implemented. TypeScript prediction remains `MODEL_UNAVAILABLE`. The feature sets below are enforced by `backend/app/analyzers/contracts.py`; they do **not** specify a model's feature ordering.

## Common persisted record

`AnalysisEntity` stores UUID `id`, `analysis_run_id`, `language`, `entity_type`, `relative_path`, `qualified_name`, one-based inclusive `start_line` / `end_line`, numeric-or-null `metrics`, `analyzer_name`, `analyzer_version`, `metric_schema_version`, and string-code `warnings`.

Identity within a run is `(language, relative_path, qualified_name, start_line)`. IDs distinguish runs; repeated runs need not produce the same UUID. Paths are relative to the prepared project root; no source text or absolute storage paths are returned. Unknown metric keys, schema/granularity mismatches, non-finite values, invalid line ranges, and escaping paths are rejected before persistence. All current analyzers supply their full numeric feature set; null is reserved for explicitly unavailable measurements, never replaced with zero to enable inference.

Results are published in one transaction with COMPLETED. Completed runs are immutable through the application. A new attempt creates another run. Parse failures are relative-path warnings; a run with some valid entities completes with warnings. No supported files produces `NO_SUPPORTED_SOURCE`; no valid entities produces `NO_ANALYZABLE_ENTITIES`. Tool failure/timeout fails the whole run without publishing partial entities.

## Java — `java_class_v1`

Tool: [CK](https://github.com/mauricioaniche/ck) **0.7.0**, shaded Maven artifact, SHA-256 `2ddfdc275b6b59c2033e03253c4fec511c338fe494a10b70f651bc039a72c74d`. KageX's wrapper uses CK's bundled Eclipse JDT **Java 11 grammar** for a syntax precheck and named-type source locations. This is not JavaParser and does not independently reimplement CK metrics. The worker uses Java 17 (verified Temurin 17.0.20.1); the actual Java runtime is recorded as `0.7.0/jdt-java11/java-<version>`.

Class-level entities use package-qualified names and `$` for nested named types. CK's named class-like units can include interfaces and enums. Anonymous/local types without a reliable matching qualified location are omitted with `JAVA_ENTITY_LOCATION_UNAVAILABLE`. Files with invalid/unsupported syntax get `FILE_PARSE_FAILED`; recovered syntax is not presented as valid metrics. Modern syntax beyond Java 11, including records, is outside this schema's supported grammar.

| Feature | Definition |
|---|---|
| `wmc` | CK weighted methods per class; sum of method complexity |
| `dit` | CK depth of inheritance tree |
| `noc` | CK number of children |
| `cbo` | CK coupling between objects |
| `rfc` | CK response for a class |
| `lcom` | CK original lack-of-cohesion measurement, not LCOM3 |
| `loc` | CK class LOC, not physical file length or necessarily the entity line span |
| `num_functions` | CK number of methods |

CK receives only copied `.java` text and a fixed classpath. Submitted JARs, build files, and dependencies are not used. Each entity carries `UNRESOLVED_DEPENDENCIES_POSSIBLE`: binding-dependent coupling/inheritance metrics may be incomplete without external dependencies. Do not assume these features equal similarly named PROMISE/D'Ambros dataset columns; Phase 4 must establish compatibility.

## Python — `python_function_v1`

Tools: [Radon](https://radon.readthedocs.io/en/latest/api.html) **6.0.1** and Python **3.14** stdlib `ast` / `tokenize`. Version metadata includes the exact Python patch version (native verification 3.14.7; Docker 3.14.8). Source is decoded using its Python encoding declaration, then parsed as text. It is never imported, compiled to executable code, or run.

Entities include module functions, methods, async functions, and nested functions. Qualified names include class scope and `<locals>` function scope. Lambdas are not separate entities. Locations start at `def` / `async def` and end at the function AST end; decorators are outside the physical line span. Counts over the function AST include nested definitions; nested definitions also receive their own entity. This overlap is deliberate and must be retained in dataset extraction.

| Feature | Definition |
|---|---|
| `loc` | Inclusive physical function span, including internal blank/comment lines |
| `sloc` | Radon source lines in that original span |
| `cyclomatic_complexity` | Radon root function complexity; nested closures retain separate Radon complexity |
| `halstead_volume`, `halstead_difficulty`, `halstead_effort` | Radon `h_visit_ast(function).total` measurements over that function subtree |
| `maintainability_index` | Radon `mi_visit(ast.unparse(function), multi=True)` on a normalized function rendering; comments/formatting are discarded, docstrings retained; a static index, not defect probability |
| `comment_density` | `(Radon comments + multi) / Radon loc` for the original function span; includes multiline strings under Radon's raw classification |
| `parameter_count` | Positional-only, positional, keyword-only, `*args`, `**kwargs`; includes `self`/`cls` |
| `branch_count` | Count of `If`, `IfExp`, `Match` nodes; not individual match arms |
| `loop_count` | Count of `For`, `AsyncFor`, `While` nodes; comprehensions excluded |
| `return_count` | Count of `Return` nodes |
| `num_functions` | Nested sync/async function definitions, excluding the root function |
| `num_classes` | Class definitions inside the function subtree |
| `import_count` | `Import` / `ImportFrom` statements inside the function subtree; module imports are not copied onto every function |

Syntax/encoding/recursion failures skip the file with `FILE_PARSE_FAILED`. Valid function bodies with multiline strings are tested. Parser memory exhaustion or external-process failure fails the run safely. Radon's estimated bug count is deliberately not exposed.

## JavaScript — `javascript_file_v1`

Tools: [ESLint Linter API](https://eslint.org/docs/latest/integrate/nodejs-api) **10.12.0**, [ts-morph](https://ts-morph.com/setup/) **28.0.0**, its locked TypeScript parser, and Node **24.14.0** in Docker. Exact ESLint/ts-morph/TypeScript/Node versions are persisted. File identity is its relative path.

Fixed ESLint configuration: ECMAScript 2025, JSX allowed, module source type except `.cjs` commonjs, classic complexity rule with threshold zero. `noInlineConfig` prevents submitted comments disabling the rule. No config discovery, repository plugin, processor, custom parser, or repository `node_modules` is loaded.

| Feature | Definition |
|---|---|
| `loc` | Physical file lines, excluding a trailing empty split caused by the final newline |
| `num_functions` | TypeScript AST function-like nodes with a body; includes arrows, methods, constructors/accessors; excludes bodyless declarations |
| `num_classes` | Class declarations and expressions |
| `import_count` | Import declarations, re-exports with a module specifier, dynamic import calls, syntactic `require(...)` calls, and external import-equals declarations |
| `coupling` | Number of distinct literal string dependency specifiers in the above constructs; no module resolution; not Java CBO |
| `cyclomatic_complexity` | Sum of ESLint classic complexity diagnostics across measured function/initializer/static-block units; top-level program decisions are not added |
| `max_function_complexity` | Maximum complexity among those ESLint units (including initializer/static-block units), zero if none |
| `complexity_units` | Number of ESLint units measured, not necessarily `num_functions` |

`require` is identified syntactically, even if shadowed. Nonliteral imports contribute to `import_count` but not literal `coupling`. A file with no measured complexity unit has zero aggregate complexity. These are not Radon function CC or CK WMC. ESLint or TypeScript syntax rejection yields `FILE_PARSE_FAILED`.

## TypeScript — `typescript_file_v1`

Tool: ts-morph **28.0.0**, using its locked TypeScript **6.0.2** parser. Same file identity and definitions for `loc`, `num_functions`, `num_classes`, `import_count`, `coupling` as the structural JS metrics above. The additional `decision_count` counts `if`, ternary, `for`, `for-in`, `for-of`, `while`, `do`, `catch`, non-default `case` nodes, and binary `&&`, `||`, `??` operators. It is explicitly **not** ESLint cyclomatic complexity. Optional chaining and logical assignments are not added to this structural count.

The project exists entirely in memory with `noLib`, `noResolve`, no tsconfig discovery, and no dependency resolution. Type errors caused by missing imports are not syntax failures. No emit, scripts, build, package installation, project config, or compiler plugins run. JSX/TSX syntax is parsed. TS overload signatures without bodies do not count as functions. Prediction capability remains `MODEL_UNAVAILABLE`; no probability/risk field exists.

## Discovery, runtime, and compatibility

Supported extensions (case-insensitive): `.java`, `.py`, `.js`, `.jsx`, `.mjs`, `.cjs`, `.ts`, `.tsx`, `.mts`, `.cts`. Other files increment `unsupported_files`; they are never executed or recursively unpacked. Binary-looking supported files containing NUL bytes and supported files over the analysis file limit are skipped with explicit warnings.

Default limits: 2000 filesystem entries (including implicit directories), 100 MiB source total, depth 32, 512 KiB per analyzed file, 10,000 entities, 8 MiB output per tool stream, 45 seconds per analyzer, 120 seconds per run, and 600 seconds queued. The discovery entry count can exceed the ZIP entry count when paths create implicit directories. Run `supported_files` counts supported files admitted to parsers, including later parse failures; skipped supported files appear in warnings. `languages` describes admitted file groups, not a claim that every group yielded entities. `warning_count` includes run/file warnings and entity warnings.

Worker source storage is read-only; safe regular files are copied into a private temporary directory. Subprocess commands are fixed arrays, without a shell, with a minimal environment and no application secrets. Linux parent-death protection kills analyzers if their task process dies. CPU, output, tool wall-clock, and Celery soft/hard deadlines apply. Python parser address space is limited to 512 MiB; Java heap to 512 MiB; Node old space to 256 MiB. Compose worker limits are 2 GiB memory, 128 PIDs, and a 512 MiB temporary filesystem. Native operation requires Linux and equivalent operator-managed container/resource limits for full isolation.

Temporary directories are removed on normal completion/failure. After hard worker/host death, restart the worker container to discard its private tmpfs; native operators must remove confirmed orphan `kagex-analysis-*` directories with workers stopped. Prepared project source follows the separate Phase 2 retention rule until project deletion. A worker crash may leave a RUNNING record; redelivery can retry within the original deadline, and reads/new-run/delete requests expire stale runs to FAILED. There is no periodic sweeper or automatic endless retry.

Future models must match language, entity granularity, schema, feature definitions and order, preprocessing, and relevant tool/runtime versions. Bump the schema for semantic changes and establish dataset comparability explicitly. Similar metric names across languages are not interchangeable. No model training, dataset ingestion, inference, SHAP, risk, or recommendation behavior is introduced by these contracts.
