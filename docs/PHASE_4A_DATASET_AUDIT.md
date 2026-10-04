# Phase 4A — dataset acquisition, provenance and audit

Status: **COMPLETE / FROZEN**. Hosted CI: **PASS**. Phase 4B: **READY**.
Audit date: 2026-10-04. Phase 3 baseline: `42c1855`. Phase 4A implementation: `7bbf452`;
owner confirmed hosted CI success (all green in GitHub Actions).

## Scope and continuation

The initial repository contained the completed Phase 3 implementation, with a clean
worktree and no Phase 4A tooling/manifests. Existing analyzers, APIs, migrations,
frontend, Docker and CI were preserved. This work adds a standalone acquisition CLI,
descriptive audits, five manifests, offline tests and documentation. No dependency
was added. No model training, preprocessing, feature extraction, label construction,
splits, selection, balancing, inference or Phase 4B implementation took place.

Acquisition is deliberately bounded: complete selected Java deposits/static tables,
BugsInPy metadata repository, BugsJS metadata plus one representative coverage
archive, and PyTraceBugs repository documentation. `ACQUIRED` means the manifest's
stated scope was acquired; it never means a complete training corpus is ready.

## Sources and provenance

| Manifest ID | Authoritative source / resolved version | Acquired scope | License evidence / status |
|---|---|---|---|
| `java_jureczko_zenodo_268440_268458` | [Ant deposit](https://zenodo.org/records/268440), [jEdit deposit](https://zenodo.org/records/268458); fixed record IDs | Six CSVs and jEdit README; 2 projects, 6 project/version tables | CC-BY-4.0 in both record API metadata; ACQUIRED |
| `java_dambros_msr2010_snapshot` | [Original USI artifact](https://bug.inf.usi.ch/download.php); upstream immutable version unknown/null | All five single-version CK/OO CSVs plus description/download HTML | No explicit dataset license found; unknown/null; ACQUIRED |
| `python_bugsinpy_11c5f1eea954` | [Official repository](https://github.com/soarsmu/BugsInPy/tree/11c5f1eea954a42132cfd06bf257766a7963e0fd); `11c5f1eea954a42132cfd06bf257766a7963e0fd` | ZIP and 2,375 inert extracted files; metadata/patches | No license-named file in acquired repository; unknown/null; ACQUIRED |
| `python_pytracebugs_89a09db9add3` | [Official repository](https://github.com/acheshkov/pytracebugs/tree/89a09db9add3ec174e3828b83e1792c6fc6ad5d2); `89a09db9add3ec174e3828b83e1792c6fc6ad5d2` | README and LICENSE only | MIT repository license; external data rights unverified; PARTIAL_METADATA |
| `javascript_bugsjs_7abbad3e4df1` | [Official repository](https://github.com/BugsJS/bug-dataset/tree/7abbad3e4df12cd5294110bb5db11b7d5bc758a6); `7abbad3e4df12cd5294110bb5db11b7d5bc758a6` | 37 artifacts: metadata/command CSVs, docs/license, inert framework text, 10 subject-repository tag-ref snapshots, Bower-1 coverage ZIP | MIT repository LICENSE; subject project rights separate; ACQUIRED |

Research references: [Jureczko/Madeyski](https://doi.org/10.1145/1868328.1868342),
[D'Ambros/Lanza/Robbes MSR 2010](https://marcodambros.gitlab.io/publications/msr10.pdf),
[BugsInPy repository](https://github.com/soarsmu/BugsInPy),
[PyTraceBugs APSEC 2021](https://doi.org/10.1109/APSEC53868.2021.00022),
[BugsJS ICST 2019](https://bugsjs.github.io/paper/ICST19.pdf).

The official PROMISE CK index links the Zenodo deposits. Ant/jEdit are a declared
subset, not the entire Jureczko collection. Unavailable guessed legacy URLs were
not replaced with third-party mirrors. D'Ambros history/churn archives and BugsJS'
remaining large coverage archives/source histories were not needed for this
structure audit and were not downloaded. API tag responses are dated snapshots,
not immutable GitHub resources; their exact bytes are checksum-frozen.

## Data directory, checksums and reproduction

```text
data/
  raw/java/<dataset-id>/         # ignored, immutable acquired bytes
  raw/python/<dataset-id>/       # ignored, inert metadata/source archives
  raw/javascript/<dataset-id>/   # ignored, metadata/representative archive
  interim/                      # ignored; unused in 4A
  processed/                    # ignored; unused in 4A
  manifests/<dataset-id>.json    # five tracked-intent JSON manifests
```

Run from `backend`, after the existing `uv sync --locked` setup:

```sh
uv run python -m app.datasets list
uv run python -m app.datasets acquire all
uv run python -m app.datasets verify all
uv run python -m app.datasets audit all
uv run pytest tests/test_datasets.py
```

Every command except `list` accepts one exact listed ID or `all`. No arbitrary URL
argument exists. Valid local acquisitions are checksum-verified without network
requests. A fresh checkout uses the committed manifests to verify downloads;
corrupt or changed files fail without overwriting raw data or provenance. Inspect
and resolve changes manually; do not delete a manifest merely to accept changed
upstream bytes. `audit` prints a fresh descriptive profile without modifying data.

There are **54 downloaded artifacts (5,918,906 bytes)**, plus **2,375 extracted
files**. Each has a SHA-256 entry. Initial SHA-256 values were measured over the
approved-source downloads, not independently supplied by authors. Zenodo CSVs also
passed upstream published MD5 checks. Manifest timestamps record acquisition time;
resolved Git commit pins and dataset scope are explicit. Profile fields record
columns, counts, labels and limitations; unknown information remains null. Java
project/version inventories retain both artifact filenames and actual CSV values.

No raw data is intended for Git. Manifests store hashes and provenance/metadata,
not benchmark source text. CI validates them and fixture-based tooling offline;
it does not acquire these datasets. Raw/interim/processed are ignored. Empty
interim/processed directories contain no fabricated output and need not survive Git.

## Java audit

Both sources have class identifiers and recorded defect counts. The following
positive counts are descriptive counts of existing values greater than zero;
no target column or new labels were created.

| Source/table | Version recorded in rows | Classes | Zero defects | Positive defects | Positive fraction |
|---|---|---:|---:|---:|---:|
| Jureczko Ant 1.7 | `1.7` | 745 | 579 | 166 | 22.28% |
| Jureczko jEdit 3.2 filename | `3.2.1` | 272 | 182 | 90 | 33.09% |
| Jureczko jEdit 4.0 filename | `4` | 306 | 231 | 75 | 24.51% |
| Jureczko jEdit 4.1 | `4.1` | 312 | 233 | 79 | 25.32% |
| Jureczko jEdit 4.2 | `4.2` | 367 | 319 | 48 | 13.08% |
| Jureczko jEdit 4.3 | `4.3` | 492 | 481 | 11 | 2.24% |
| D'Ambros Eclipse JDT | unknown in acquired CSV | 997 | 791 | 206 | 20.66% |
| D'Ambros Equinox | unknown in acquired CSV | 324 | 195 | 129 | 39.81% |
| D'Ambros Lucene | unknown in acquired CSV | 691 | 627 | 64 | 9.26% |
| D'Ambros Mylyn | unknown in acquired CSV | 1,862 | 1,617 | 245 | 13.16% |
| D'Ambros Eclipse PDE | unknown in acquired CSV | 1,497 | 1,288 | 209 | 13.96% |

Jureczko totals **2,494 rows**, D'Ambros **5,371**, combined **7,865**. There are no
malformed rows, duplicate full rows, duplicate class identities within any table,
missing class identifiers or invalid defect counts in these acquired tables.
Jureczko has no missing cells. D'Ambros has a trailing delimiter producing one empty
column on every row; all named columns are populated. This formatting artifact is
recorded, not silently cleaned.

Jureczko has duplicate header name `name`: first is project, third is class. The
audit keeps column indexes and raw headers, avoiding lossy DictReader overwrites.
Its 20 metric columns are `wmc, dit, noc, cbo, rfc, lcom, ca, ce, npm, lcom3, loc,
dam, moa, mfa, cam, ic, cbm, amc, max_cc, avg_cc`; label is `bug`. Filename and row
version discrepancies above are preserved. Across tables there are **1,422**
distinct `(project, class)` identities; **367** recur across versions, accounting
for **1,072** repeat observations. These are versioned observations, not rows to
delete. Any later evaluation must address their leakage risk.

D'Ambros' class key is `classname`; its 17 metrics are `cbo, dit, fanIn, fanOut,
lcom, noc, numberOfAttributes, numberOfAttributesInherited, numberOfLinesOfCode,
numberOfMethods, numberOfMethodsInherited, numberOfPrivateAttributes,
numberOfPrivateMethods, numberOfPublicAttributes, numberOfPublicMethods, rfc, wmc`.
Labels are `bugs, nonTrivialBugs, majorBugs, criticalBugs, highPriorityBugs`;
the audit distribution uses `bugs`. Upstream describes post-release bug counts.
Severity/priority counts must not become predictors of that same defect outcome.
Only single-version tables were acquired, not D'Ambros' historical model series.
Exact release dates/versions are unestablished and must not be inferred from names.
Min/max/median and missingness for numeric fields are in each manifest.

## Python audit

**BugsInPy:** 501 bug instances across 17 projects. Counts: PySnooper 3, ansible 18,
black 23, cookiecutter 4, fastapi 16, httpie 5, keras 45, luigi 33, matplotlib 30,
pandas 169, sanic 5, scrapy 40, spacy 10, thefuck 32, tornado 16, tqdm 9,
youtube-dl 43. These are measured at the acquired commit, not paper-era counts.

`project.info` records repository URLs; `bug.info` records buggy/fixed revisions,
Python versions, test-file paths and occasionally pythonpath. `bug_patch.txt`
provides textual changed-file/hunk evidence. Requirements, setup scripts and test
runners are inert files, never executed. Manifest inventory records project/bug,
literal revisions, test paths and patch paths. No source revision was checked out.

All metadata pairs have syntactically hexadecimal revisions, but **168 Pandas
pairs contain seven-character abbreviated IDs**. These are unresolved, not full
immutable subject-revision pins. There are no duplicated project/revision pairs.
All patch files exist; **Keras bug 12 has an empty patch and identical buggy/fixed
SHA**, so localization is absent for that record. This is flagged, not repaired.
Patch paths identify changed files, which can include tests and ancillary changes;
they do not establish every changed function as defective.

Direct function-level positive/negative sample tables and Phase 3 metric columns
are absent. Class balance and negative-function counts are null. Later static
diff/AST localization could be designed without code execution; equivalence to
the benchmark's behavioral validation would require executing tests and is outside
KageX's allowed workflow. No labels were invented here.

**PyTraceBugs:** the pinned README describes function/method buggy and stable source
snippets, bug/fix pairs, issue/traceback evidence, and existing upstream partitions.
These are documented claims, not measured dataset findings. Its documented fields
include `before_merge`, `after_merge`, filenames, full-file source, function names,
issue URL, traceback/type, stripped-source/docstring variants and snippet paths;
the test metadata adds bug descriptions/types/line ranges. Stable metadata lists
repository, commit and source paths. No numeric production metric columns are
established. Existing upstream partitions are not KageX-created splits.

The official [v1 RAR link](https://pytracebugs-dataset.obs.ap-southeast-3.myhuaweicloud.com/pytracebugs_dataset_v1.rar)
returned **HTTP 404**. Only README/LICENSE were acquired. Actual records, balance,
missingness, duplicates and label/localization quality remain **unknown/null**.
The documented tables use pickle; no pickle was loaded. **Manual action:** request
a restored versioned artifact, checksums and license scope from authors via the
official repository, preferably CSV/JSON metadata plus inert source files. Do not
substitute a mirror or deserialize untrusted pickle. No login/license acceptance
was bypassed and no message was sent to authors.

## JavaScript audit

<!-- PyTraceBugs recovery evidence is recorded separately below; other dataset audits are unchanged. -->

**BugsJS:** 453 bug rows across 10 projects: Bower 3, Eslint 333, Express 27,
Hessian.js 9, Hexo 12, Karma 22, Mongoose 29, Node-redis 7, Pencilblue 7, Shields 4.
Each project's bug CSV has a unique ID per row; no malformed/duplicate rows or
duplicate/missing IDs were found. There are **32 missing Bugfix patterns** values:
Eslint 21, Express 4, Karma 3, Mongoose 4. Raw commands CSVs were retained as inert
metadata, never run.

Bug-table columns describe test counts/results, line/statement/function/branch
coverage measurements, bug categories and fix patterns. They are not supervised
production file-metric vectors. No clean-file population or file-level class
balance is provided by this acquired scope; both remain unknown.

All 453 bug IDs have expected `Bug-ID`, `Bug-ID-full` and `Bug-ID-test` refs in
the acquired authoritative subject-repository snapshots, and these particular refs
point to commit objects. Other release refs can be annotated tag objects: an object
SHA must not automatically be described as a peeled commit. Inert inspection of
upstream `myGit.py` establishes that the buggy revision is the **parent of `Bug-ID`**,
the fixed revision is `Bug-ID-full`, and test-only changes use `Bug-ID-test`.
`Bug-ID` itself must not be mislabeled as the buggy commit. Actual buggy parent
SHAs, source contents and changed-file diffs have not been acquired or derived.

The Bower-1 ZIP directory contains **472 members**, grouped into buggy, fixed and
test-only coverage/metrics outputs, including nested ZIPs. Only its directory was
listed; nested files/binaries were not unpacked or deserialized. One inspected
archive does not validate every bug archive. Source-file localization and a
defensible negative-file policy remain future work. Static revision diffs can be
used without tests; this phase does not attempt behavioral benchmark reproduction.

## Feature mapping and licensing

[PHASE_4A_FEATURE_REFERENCE.md](PHASE_4A_FEATURE_REFERENCE.md) accounts for all
37 actual Phase 3 features and exact tool/schema versions. Statuses are limited to
candidate/review/derived/unavailable meanings; no feature is marked compatible.
TypeScript has no approved defect dataset and remains **MODEL_UNAVAILABLE**.

The Zenodo license applies to those archival deposits; BugsJS/PyTraceBugs MIT files
are repository evidence. They do not establish blanket rights over all underlying
subject projects/snippets. D'Ambros and BugsInPy licensing remains ambiguous.
No commercial/SaaS redistribution entitlement is asserted. Training/distribution
scope needs evidence before later phases. Earlier planning statements in TD-002–004
are not substitutes for acquired license and feature-definition evidence.

## Safety, tests and CI

Downloads use fixed allowlisted HTTPS sources, no credentials/environment proxies
or redirects, 100 MiB per artifact, 20-second network-operation timeouts and a
120-second checked download deadline (an in-progress read can finish after it).
Staging is private and failure-cleaned. BugsInPy extraction reuses unchanged Phase 2
ZIP traversal/link/CRC/count/ratio defenses, with explicit dataset limits: 100 MiB
compressed, 1 GiB expanded, 100 MiB per file, 10,000 entries, ratio 100 and 120-second
extraction deadline. No recursive archive extraction occurs. CSV parsing is bounded
to 1 MiB fields and 250,000 records; raw artifacts are capped by download limits.
Downloaded HTML and scripts were read as text, not rendered or executed.

No benchmark/project code, tests, hooks, binaries or setup/install scripts ran.
No benchmark dependencies were installed. No unsafe pickle/joblib load exists in
the acquisition code. API/worker/analyzer production behavior is unchanged.
Existing extractor security tests remain relevant and pass alongside new tooling
fixtures. Checksums detect accidental/source drift; they are not a signature from
the dataset author, nor a defense against someone editing both data and manifests.

Local verification: **118 distinct backend tests pass**: **13 dataset tests** and
the **105 existing regression tests**. The full run passed 117 tests before one
additional JavaScript audit fixture was added; the final focused run passed all
13 dataset tests after the remaining audit-only changes. Ruff lint/format and mypy pass on **54 Python
files**. All five manifests and local inventories validate, and freshly computed
profiles exactly match their recorded profiles. Frontend/Docker files
are unchanged; their prior Phase 3 gates were already green and were not rerun for
this standalone offline tooling. CI's existing pytest command discovers these new
tests without network/dataset downloads. No new CI workflow is necessary.

Hosted CI for Phase 4A has run and passed (**PASS**, confirmed green by the project
owner for delivered commit `7bbf452`). All backend tests, linting, formatting, and
type checks passed in GitHub Actions.

## Phase 4A acceptance matrix

| Criterion | Status | Evidence / limitation |
|---|---|---|
| Approved authoritative sources only | PASS | Five fixed catalog entries; no substitute dataset |
| Existing valid implementation preserved | PASS | Phase 3 production files untouched |
| Dataset provenance and research references | PASS | Five versioned manifests and source table |
| Versions/commits recorded where available | PASS | Full repository pins; D'Ambros version null; abbreviated subject IDs flagged |
| Acquisition dates / artifact names / SHA-256 | PASS | All 54 artifacts and 2,375 extracted files |
| Actual license evidence and ambiguity recorded | PASS | CC-BY-4.0 / repository MIT / explicit unknown |
| Reproducible acquisition and offline reuse | PASS | Fixed sources, checksum checks, fixture tests |
| Corrupt/partial downloads fail without overwrite | PASS | Checksum/truncation/limit/preservation fixtures |
| Raw/large data ignored; no secrets staged | PASS | Git hygiene checks; `.env` untouched |
| Java approved data acquired | PASS | Declared Ant/jEdit subset and five D'Ambros static tables |
| Java class granularity and identifiers | PASS | Actual rows and original documentation |
| Java labels / feature columns inventoried | PASS | Indexed raw headers and defect distributions |
| Java projects/versions and repeated identities | PASS | Tables above; version ambiguity retained |
| Java imbalance/missingness/duplicates profiled | PASS | 7,865 rows; descriptive profiles |
| BugsInPy acquired and audited | PASS | 501 bugs / 17 projects; patch/revision findings |
| PyTraceBugs acquired or exact blocker documented | PASS | Acquired via Wayback Machine preservation of official URL; SHA-1/SHA-256 verified |
| Full PyTraceBugs contents inspected | PASS | Bounded libarchive inspection: 47,172 entries, buggy/stable datasets, inert AST samples; no pickle deserialization |
| Python bug representation / localization assessed | PASS | Full metadata and explicit limitations |
| Python function supervision availability assessed | PASS | BugsInPy derivation needed; PyTrace documented only |
| No fabricated Python labels | PASS | No derived targets; unknown counts null |
| BugsJS acquired and audited | PASS | Declared metadata/sample scope, 453 bugs / 10 projects |
| JavaScript revisions/localization assessed | PASS | Ref snapshots and verified upstream parent rule |
| JavaScript direct file supervision assessed | PASS | Absent from acquired scope; derivation unresolved |
| TypeScript MODEL_UNAVAILABLE / no substitution | PASS | No TypeScript dataset or model work |
| Actual Phase 3 feature/version candidate reference | PASS | All 37 features documented |
| No premature feature compatibility claims | PASS | Definition review/derived/unavailable statuses |
| No training/transforms/splits/artifacts/inference | PASS | Acquisition/descriptive audit only |
| No source execution or benchmark installs | PASS | Inert read/parse/extract paths and review |
| Acquisition / manifest / security tests | PASS | Offline fixtures plus existing security regression tests |
| Lint / format / type checks | PASS | Ruff and mypy, 54 files |
| Relevant existing regression suite | PASS | All 105 existing backend tests pass |
| New frontend/Docker implementation checks | N/A | No frontend, Docker, migration or worker changes |
| Hosted CI after Phase 4A changes | PASS | Confirmed green in GitHub Actions for commit `7bbf452` |

## Phase 4B questions and handoff

Do not begin 4B until separately authorized after the required gates. Resolve:

1. Is the declared Ant/jEdit coverage sufficient, or should additional approved
   deposits be acquired? Can D'Ambros release versions/license scope be established?
2. Which Java metrics have matching measurement definitions and tool/binding scope?
   No named column is accepted solely on its name.
3. Can BugsInPy abbreviated subject revisions be fully pinned? How should the
   identical Keras revision/empty patch be handled without fabricated supervision?
4. Can PyTraceBugs authors restore a licensed, versioned, safe-format artifact?
   If unavailable, keep it unavailable and assess the approved remaining baseline.
5. What defensible static-only localization and negative-sample policy can support
   Python functions and JavaScript files, with tests/config changes excluded?
6. How will project/version/repeated-source leakage and historical parser support
   be evaluated later, without executing code or constructing splits in 4A?
7. What license evidence permits the intended training and distribution scope?

Current internal checklist: COMPLETE — scoped acquisition, profiles, manifests,
feature reference, local checks, PyTraceBugs archival acquisition/inspection,
independent verification, and hosted GitHub Actions CI; REMAINING — None;
BLOCKED — None. Phase 4A is COMPLETE / FROZEN. Phase 4B is READY.

## PyTraceBugs recovery investigation — 2026-10-04

This follow-up is limited to PyTraceBugs. It started from clean repository head
`1f57071`; no other dataset files or manifests are changed. No local file named
`pytracebugs_dataset_v1.rar` existed at inspection, so there was no invalid local
XML file to remove. A fresh request to the original URL returned **HTTP 404,
application/xml, 329 bytes, `NoSuchBucket`**, not a RAR signature. Those error
bytes were never stored as a dataset artifact or assigned a dataset checksum.

The official repository's current master is still the approved
`89a09db9add3ec174e3828b83e1792c6fc6ad5d2`. Its pinned README/LICENSE are retained.
The following sources were checked; search results alone were never treated as
proof that a copy was authoritative or complete:

| Source checked | Result |
|---|---|
| [Official current commit](https://api.github.com/repos/acheshkov/pytracebugs/commits/master), [repository contents](https://api.github.com/repos/acheshkov/pytracebugs/contents/), [README history](https://api.github.com/repos/acheshkov/pytracebugs/commits?path=README.md&per_page=100), [initial tree](https://api.github.com/repos/acheshkov/pytracebugs/git/trees/1cb4bcbf4b1849760fc385c3ec6366eaf8bb8be1?recursive=1) | Metadata repository; current pin unchanged; initial tree has no full dataset archive. |
| [Official releases](https://api.github.com/repos/acheshkov/pytracebugs/releases) and [tags](https://api.github.com/repos/acheshkov/pytracebugs/tags) | Both empty; no release assets. |
| [All official issues/PRs](https://api.github.com/repos/acheshkov/pytracebugs/issues?state=all&per_page=100), including comments on [#2](https://github.com/acheshkov/pytracebugs/issues/2), [#3](https://github.com/acheshkov/pytracebugs/issues/3), [#5](https://github.com/acheshkov/pytracebugs/issues/5) and XML report [#4](https://github.com/acheshkov/pytracebugs/issues/4) | Owner restored access in an older #3 reply; latest #5 reply supplies no replacement. #2 owner/collaborator replies identify the official pipeline repository. |
| [Author pipeline repository](https://github.com/acheshkov/pytracebugs_pipeline/tree/51709b17217e64bee54aeca0a109183de3c73c17) and [paper source](https://github.com/acheshkov/pytracebugs_pipeline/blob/51709b17217e64bee54aeca0a109183de3c73c17/papers/pytracebugs_paper/pytracebugs_apsec2021.tex) | Paper source corroborates project identity, authors, function/method samples and existing splits, and links the official metadata repository. Read as text only; no LaTeX/build/benchmark command run. |
| [Crossref DOI metadata](https://api.crossref.org/works/10.1109/APSEC53868.2021.00022), [IEEE landing page](https://ieeexplore.ieee.org/document/9712116/) | Crossref confirms title/authors/institution. IEEE response was not usable for supplementary-asset inspection; the author-maintained paper source was available instead. |
| [Authors' institutional publication listing](https://www.imm.uran.ru/rus/research_areas/science_and_universities/Pages/New_Labs.aspx) and targeted institution searches | Confirms publication association; no replacement dataset located. |
| [Zenodo search](https://zenodo.org/api/records?q=pytracebugs&size=10), [Figshare DOI search](https://api.figshare.com/v2/articles?resource_doi=10.1109%2FAPSEC53868.2021.00022) | Zero records for those queries. This is not proof that no differently indexed deposit exists. |
| [Hugging Face search](https://huggingface.co/api/datasets?search=pytracebugs) | `claudios/PyTraceBugs` has metadata only. `gurudesh/pytracebugs` lists three bugfix CSVs, without demonstrated author association or the stable collection. Neither was acquired or substituted. |
| [Kaggle search](https://www.kaggle.com/api/v1/datasets/list?search=pytracebugs) and targeted public archive searches | No matching Kaggle API result or author-endorsed full copy found. |
| [Internet Archive item search](https://archive.org/advancedsearch.php?q=pytracebugs&output=json) | No named item result. |
| [Wayback CDX query for the exact official URL](https://web.archive.org/cdx/search/cdx?url=pytracebugs-dataset.obs.ap-southeast-3.myhuaweicloud.com/pytracebugs_dataset_v1.rar&output=json&filter=statuscode:200&filter=mimetype:application/x-rar-compressed&collapse=digest) | Found HTTP 200 RAR capture `20230808125225`; payload digest `RVQL6UPBOMAKYJLHUSSR6SHNJ3V2RWGG` (base32 SHA-1). This is preservation of the authoritative original URL, not an unrelated mirror. |

Selected replacement:
[2023-08-08 12:52:25 UTC raw archival capture](https://web.archive.org/web/20230808125225id_/https://pytracebugs-dataset.obs.ap-southeast-3.myhuaweicloud.com/pytracebugs_dataset_v1.rar).
Replay headers identify the exact original URL and report **1,960,844,036 payload
bytes**, original modification time 2022-04-11 10:14:36 GMT, and the matching capture
time. The CDX `length` field is a WARC-record size, not the dataset payload length.
The response starts with the RAR5 signature. The captured original ETag is multipart
and is not treated as a plain MD5 checksum.

### Recovery validation and structural audit results

1. **Payload and Checksum Verification:**
   - **Target File:** `data/raw/python/python_pytracebugs_89a09db9add3/pytracebugs_dataset_v1.rar`
   - **Payload Size:** 1,960,844,036 bytes (exact match to Wayback CDX payload size)
   - **File Format:** RAR archive data, v5 (starts with signature `Rar!\x1a\x07\x01\x00`)
   - **Archival CDX SHA-1:** `8d60bf51e17300ac2567a4a51f48ed4eeba8d8c6` (exact match to base32 `RVQL6UPBOMAKYJLHUSSR6SHNJ3V2RWGG`)
   - **Local SHA-256:** `86071947daa9ec2a38a6e6af0d7f2da78fcc407e8fa12009930099de1b9fcd20`

2. **Inert Structural Audit (Host `libarchive`):**
   - The archive was audited in-memory using host system `libarchive 3.8.7` without unpacking to disk or running code.
   - **Total entries:** 47,172 (47,169 regular files, 3 directory nodes)
   - **Declared uncompressed size:** 4,777,703,344 bytes (~4.78 GB)
   - **Directory groups:**
     - `README.md`: 1 file
     - `buggy_dataset`: 3 pickle tables (`bugfixes_train.pickle`, `bugfixes_valid.pickle`, `bugfixes_test.pickle`)
     - `buggy_dataset/buggy_snippets_files`: 47,160 Python snippet files
     - `stable_dataset`: 5 files (`stable_code_train.pickle`, `stable_code_valid.pickle`, `stable_code_test.pickle`, and dataset descriptors)
   - **Pickle Security Policy:** All 6 `.pickle` tables (`deserialized: false`) were kept strictly opaque. No deserialization (`pickle.load`, `pandas.read_pickle`, or `joblib`) was performed.
   - **Python Snippet Syntax Inspection:** Sample Python snippets (e.g. `0003b2ea39ce27962210ab8b507d97ca8224706fc8b7a4b835fafcca39cfeb6f_before_merge.py` and `_after_merge.py`) were inspected strictly via `ast.parse` in text mode. Both confirmed function/method definitions present (`function_or_method_definition_present: true`, `syntax_check: "parsed_as_text_only"`). No benchmark/snippet code was imported, executed, or extracted to disk.

3. **Manifest and Catalog Updates:**
   - Manifest `data/manifests/python_pytracebugs_89a09db9add3.json` has been updated and validated with 5 artifacts:
     - `README.md` (4,684 bytes, SHA-256: `b245e64c9b0689203a393fdf9924cb14f8e2585b3f218a8ab375572e6e7cacac`)
     - `LICENSE` (1,066 bytes, SHA-256: `310300bff55e18942fa0d94c92588fd88a2a5583275e53f698253bd31f002bdd`)
     - `pytracebugs_dataset_v1.rar` (1,960,844,036 bytes, SHA-256: `86071947daa9ec2a38a6e6af0d7f2da78fcc407e8fa12009930099de1b9fcd20`, Archival SHA-1: `8d60bf51e17300ac2567a4a51f48ed4eeba8d8c6`)
     - `archive-capture.json` (246 bytes, SHA-256: `cb9ac0586fd1db33064acbb5c9213006ccd8d0c7c5e63a0acd5e20253c46c372`)
     - `author-paper.tex` (61,307 bytes, SHA-256: `873f38567ae06eec76d204c03d8a75e862e85e33b41d5750785ec9a26653a482`)
   - `acquisition_status` is updated to `ACQUIRED` (blocker: `None`).
   - Catalog in `backend/app/dataset_sources.py` records source URLs, bounds, and SHA-1 matching the preservation evidence.

4. **License and Usage Boundaries:**
   - Repository license is MIT (`LICENSE` file pinned to commit `89a09db9add3ec174e3828b83e1792c6fc6ad5d2`).
   - Underlying code snippets and dataset archive require separate license review. Archival access grants no additional redistribution rights.
   - The recovery does not validate pickle table contents, establish Phase 3 feature compatibility, create labels/splits, or authorize starting Phase 4B.
