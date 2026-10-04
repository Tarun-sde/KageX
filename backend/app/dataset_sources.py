"""Approved Phase 4A sources only. These are data, never executable dependencies."""

from string import ascii_letters, digits
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, field_validator

PYTRACE_ORIGINAL = (
    "https://pytracebugs-dataset.obs.ap-southeast-3.myhuaweicloud.com/"
    "pytracebugs_dataset_v1.rar"
)
PYTRACE_CAPTURE = "20230808125225"
PYTRACE_ARCHIVE = f"https://web.archive.org/web/{PYTRACE_CAPTURE}id_/{PYTRACE_ORIGINAL}"
PYTRACE_ARCHIVE_BYTES = 1960844036
PYTRACE_CDX_SHA1 = "8d60bf51e17300ac2567a4a51f48ed4eeba8d8c6"


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filename: str
    url: str
    extract_zip: bool = False
    upstream_md5: str | None = None
    upstream_sha1: str | None = None

    @field_validator("filename")
    @classmethod
    def safe_filename(cls, value: str) -> str:
        if (
            not value
            or any(c not in ascii_letters + digits + "._-" for c in value)
            or value in {".", ".."}
        ):
            raise ValueError("Expected a flat artifact filename")
        return value

    @field_validator("url")
    @classmethod
    def approved_host(cls, value: str) -> str:
        url = urlsplit(value)
        if (
            url.scheme != "https"
            or url.hostname
            not in {
                "zenodo.org",
                "bug.inf.usi.ch",
                "codeload.github.com",
                "raw.githubusercontent.com",
                "api.github.com",
                "web.archive.org",
            }
            or url.username
            or url.password
            or url.fragment
            or url.port not in {None, 443}
        ):
            raise ValueError("Unapproved source URL")
        return value


class Dataset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataset_id: str
    canonical_name: str
    language: Literal["java", "python", "javascript"]
    source_type: str
    upstream: str
    version: str | None
    license: str | None
    license_scope: str
    reference: str
    granularity: str
    label_semantics: str
    scope: str
    acquisition_status: Literal["ACQUIRED", "PARTIAL_METADATA"] = "ACQUIRED"
    blocker: str | None = None
    sources: list[Source]


BUGSINPY = "11c5f1eea954a42132cfd06bf257766a7963e0fd"
PYTRACEBUGS = "89a09db9add3ec174e3828b83e1792c6fc6ad5d2"
BUGSJS = "7abbad3e4df12cd5294110bb5db11b7d5bc758a6"
JS_PROJECTS = {
    "Bower": "bower",
    "Eslint": "eslint",
    "Express": "express",
    "Hessian.js": "hessian.js",
    "Hexo": "hexo",
    "Karma": "karma",
    "Mongoose": "mongoose",
    "Node-redis": "node_redis",
    "Pencilblue": "pencilblue",
    "Shields": "shields",
}


def github_file(repo: str, commit: str, path: str) -> Source:
    return Source(
        filename=path.replace("/", "__"),
        url=f"https://raw.githubusercontent.com/{repo}/{commit}/{path}",
    )


def sources() -> dict[str, Dataset]:
    datasets = [
        Dataset(
            dataset_id="java_jureczko_zenodo_268440_268458",
            canonical_name="PROMISE/Jureczko — authoritative Ant and jEdit deposits",
            language="java",
            source_type="authoritative_archive",
            upstream=(
                "https://zenodo.org/records/268440; https://zenodo.org/records/268458"
            ),
            version="Zenodo records 268440 and 268458 (v1 deposits)",
            license="CC-BY-4.0",
            license_scope=(
                "Dataset deposit metadata; not a license for underlying project source."
            ),
            reference="https://doi.org/10.1145/1868328.1868342",
            granularity="class",
            label_semantics=(
                "bug: reported defect count per class; audit counts zero versus "
                "positive without creating labels."
            ),
            scope=(
                "Complete files of these two deposits only; not the entire "
                "Jureczko collection. Ant 1.7 and jEdit 3.2/4.0/4.1/4.2/4.3."
            ),
            sources=[
                Source(
                    filename=name,
                    url=f"https://zenodo.org/api/records/{record}/files/{name}/content",
                    upstream_md5=checksum,
                )
                for record, name, checksum in [
                    (268440, "ant-1.7.csv", "d99a6698b92553abb285df838e03dcbb"),
                    (268458, "README.txt", "59bc81633f6be2eff51280a40638b447"),
                    (268458, "jedit-3.2.csv", "508ea13bcfd3d556a7b88d61da40abb0"),
                    (268458, "jedit-4.0.csv", "c55ca83778cc61dfdafbde1293c2221e"),
                    (268458, "jedit-4.1.csv", "0b8307cc6452b1a67967c025fd73e46f"),
                    (268458, "jedit-4.2.csv", "3884e4673ffb3a3044ddc609eca30eb2"),
                    (268458, "jedit-4.3.csv", "a4d059d56f7d4de1339fd83ad9f29dc2"),
                ]
            ],
        ),
        Dataset(
            dataset_id="java_dambros_msr2010_snapshot",
            canonical_name=(
                "D'Ambros bug prediction dataset — single-version CK/OO tables"
            ),
            language="java",
            source_type="original_research_artifact",
            upstream="https://bug.inf.usi.ch/download.php",
            version=None,
            license=None,
            license_scope=(
                "No explicit dataset license found on original "
                "description/download pages; underlying project licenses are "
                "separate."
            ),
            reference="https://marcodambros.gitlab.io/publications/msr10.pdf",
            granularity="class",
            label_semantics=(
                "bugs and categorized post-release defect counts; count fields "
                "remain unchanged."
            ),
            scope=(
                "All five published single-version CK/OO CSV tables. "
                "Historical/churn/entropy archives are not acquired. Upstream has "
                "no immutable release ID; freeze downloaded bytes by SHA-256."
            ),
            sources=[
                Source(
                    filename=f"{project}.csv",
                    url=f"https://bug.inf.usi.ch/data/{project}/single-version-ck-oo.csv",
                )
                for project in ["eclipse", "pde", "equinox", "lucene", "mylyn"]
            ]
            + [
                Source(
                    filename=f"{page}.html", url=f"https://bug.inf.usi.ch/{page}.php"
                )
                for page in ["index", "download"]
            ],
        ),
        Dataset(
            dataset_id=f"python_bugsinpy_{BUGSINPY[:12]}",
            canonical_name="BugsInPy",
            language="python",
            source_type="official_repository",
            upstream="https://github.com/soarsmu/BugsInPy",
            version=BUGSINPY,
            license=None,
            license_scope=(
                "No repository license found at this commit; do not infer "
                "MIT/Apache from benchmark subjects."
            ),
            reference=f"https://github.com/soarsmu/BugsInPy/tree/{BUGSINPY}",
            granularity=(
                "bug instance with project revisions and patches; function "
                "supervision requires review"
            ),
            label_semantics=(
                "Curated buggy/fixed commit pair. Function-level labels and "
                "negative examples are not directly provided."
            ),
            scope=(
                "Complete pinned benchmark metadata repository; subject repository "
                "revisions are not checked out or executed."
            ),
            sources=[
                Source(
                    filename="bugsinpy.zip",
                    url=f"https://codeload.github.com/soarsmu/BugsInPy/zip/{BUGSINPY}",
                    extract_zip=True,
                )
            ],
        ),
        Dataset(
            dataset_id=f"python_pytracebugs_{PYTRACEBUGS[:12]}",
            canonical_name="PyTraceBugs",
            language="python",
            source_type="official_repository_and_archival_preservation",
            upstream="https://github.com/acheshkov/pytracebugs",
            version=PYTRACEBUGS,
            license="MIT",
            license_scope=(
                "Repository LICENSE only; archived dataset and underlying snippets "
                "require separate license review. Archival access grants no new rights."
            ),
            reference="https://doi.org/10.1109/APSEC53868.2021.00022",
            granularity=(
                "function/method snippets; archive structure and bounded inert "
                "samples audited"
            ),
            label_semantics=(
                "Upstream buggy/stable collections with existing train/validation/test "
                "partitions. Pickle tables remain opaque; labels are not recreated."
            ),
            scope=(
                "Pinned README/LICENSE and author paper source; full original v1 RAR "
                "preserved by Internet Archive at 20230808125225 plus CDX evidence. "
                "Original host returns HTTP 404 NoSuchBucket. Archive size, RAR5 "
                "signature, archival SHA-1, local SHA-256 and inert structure checked. "
                "No pickle deserialization or model work."
            ),
            sources=[
                github_file("acheshkov/pytracebugs", PYTRACEBUGS, path)
                for path in ["README.md", "LICENSE"]
            ]
            + [
                Source(
                    filename="pytracebugs_dataset_v1.rar",
                    url=PYTRACE_ARCHIVE,
                    upstream_sha1=PYTRACE_CDX_SHA1,
                ),
                Source(
                    filename="archive-capture.json",
                    url=(
                        "https://web.archive.org/cdx/search/cdx?url="
                        f"{PYTRACE_ORIGINAL}&output=json&filter=timestamp:{PYTRACE_CAPTURE}"
                        "&fl=timestamp,original,mimetype,statuscode,digest"
                        "&filter=statuscode:200"
                    ),
                ),
                Source(
                    filename="author-paper.tex",
                    url=(
                        "https://raw.githubusercontent.com/acheshkov/pytracebugs_pipeline/"
                        "51709b17217e64bee54aeca0a109183de3c73c17/"
                        "papers/pytracebugs_paper/pytracebugs_apsec2021.tex"
                    ),
                ),
            ],
        ),
        Dataset(
            dataset_id=f"javascript_bugsjs_{BUGSJS[:12]}",
            canonical_name="BugsJS",
            language="javascript",
            source_type="official_repository_metadata",
            upstream="https://github.com/BugsJS/bug-dataset",
            version=BUGSJS,
            license="MIT",
            license_scope=(
                "Benchmark framework/data repository LICENSE; subject source "
                "licenses remain separate."
            ),
            reference="https://bugsjs.github.io/paper/ICST19.pdf",
            granularity=(
                "bug instance; file-level supervised samples require derivation"
            ),
            label_semantics=(
                "Curated bug IDs with buggy/fixed/fixed-only-test-change "
                "revisions; existing counts are test/coverage measurements, not "
                "Phase 3 file metrics."
            ),
            scope=(
                "All project/bug/command CSV metadata, revision tag metadata, "
                "documentation/license and one inert Bower coverage archive. Full "
                "subject histories and large per-test coverage archives are not "
                "acquired."
            ),
            sources=[
                github_file("BugsJS/bug-dataset", BUGSJS, path)
                for path in [
                    "Projects.csv",
                    "README.md",
                    "LICENSE",
                    "myGit.py",
                    "myVersion.py",
                    "project.proto",
                ]
            ]
            + [
                github_file(
                    "BugsJS/bug-dataset",
                    BUGSJS,
                    f"Projects/{project}/{project}_{kind}.csv",
                )
                for project in JS_PROJECTS
                for kind in ["bugs", "commands"]
            ]
            + [
                Source(
                    filename=f"{project}-refs.json",
                    url=f"https://api.github.com/repos/BugsJS/{repo}/git/matching-refs/tags/",
                )
                for project, repo in JS_PROJECTS.items()
            ]
            + [github_file("BugsJS/bug-dataset", BUGSJS, "Projects/Bower/Bower-1.zip")],
        ),
    ]
    return {dataset.dataset_id: dataset for dataset in datasets}
