import hashlib
import io
import json
import stat
import zipfile
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.dataset_audit import bugsinpy_profile, bugsjs_profile, csv_profile
from app.dataset_sources import (
    BUGSINPY,
    PYTRACE_ARCHIVE,
    PYTRACE_ARCHIVE_BYTES,
    Dataset,
    Source,
    sources,
)
from app.datasets import (
    DATA,
    MAX_BYTES,
    Artifact,
    acquire,
    checksum,
    download,
    read_manifest,
    verify,
)

CSV = b"name,version,name,wmc,bug\nproject,1,A,2,0\nproject,1,B,3,2\n"


@pytest.fixture
def catalog(monkeypatch: pytest.MonkeyPatch) -> Dataset:
    dataset = next(iter(sources().values())).model_copy(
        update={
            "sources": [
                Source(filename="fixture.csv", url="https://bug.inf.usi.ch/fixture.csv")
            ]
        }
    )
    monkeypatch.setattr("app.datasets.sources", lambda: {dataset.dataset_id: dataset})
    return dataset


def response(
    monkeypatch: pytest.MonkeyPatch, content: bytes, length: int | None = None
) -> None:
    class Response(io.BytesIO):
        headers = {"Content-Length": str(len(content) if length is None else length)}

    class Opener:
        def open(self, *args: Any, **kwargs: Any) -> Response:
            return Response(content)

    monkeypatch.setattr(
        "app.datasets.urllib.request.build_opener", lambda *args: Opener()
    )


def test_acquisition_manifest_and_existing_offline_detection(
    catalog: Dataset, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    response(monkeypatch, CSV)
    manifest = acquire(catalog.dataset_id, tmp_path)
    path = tmp_path / "manifests" / f"{catalog.dataset_id}.json"
    assert read_manifest(path) == manifest
    assert manifest.artifacts[0].sha256 == hashlib.sha256(CSV).hexdigest()
    root = tmp_path / "raw" / "java" / catalog.dataset_id
    assert checksum(root / "fixture.csv") == manifest.artifacts[0].sha256
    root.rename(tmp_path / "preserved-first-download")
    assert acquire(catalog.dataset_id, tmp_path) == manifest
    assert read_manifest(path) == manifest  # Cold acquisition preserves provenance.

    def no_download(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Existing verified datasets must not use the network")

    monkeypatch.setattr("app.datasets.download", no_download)
    assert acquire(catalog.dataset_id, tmp_path) == manifest
    (root / "fixture.csv").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="refusing to overwrite"):
        acquire(catalog.dataset_id, tmp_path)
    assert (root / "fixture.csv").read_bytes() == b"corrupt"


@pytest.mark.parametrize(
    "kind", ["checksum", "archival_sha1", "incomplete", "oversized"]
)
def test_bad_downloads_are_not_published(
    kind: str, catalog: Dataset, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = catalog.sources[0]
    if kind == "archival_sha1":
        source = source.model_copy(update={"upstream_sha1": "0" * 40})
    expected = Artifact(**source.model_dump(), sha256="0" * 64, size_bytes=len(CSV))
    length = (
        len(CSV) + 1
        if kind == "incomplete"
        else (MAX_BYTES + 1 if kind == "oversized" else len(CSV))
    )
    response(monkeypatch, CSV, length)
    target = tmp_path / "download.csv"
    with pytest.raises(ValueError):
        download(source, target, expected if kind == "checksum" else None)
    assert not target.exists()


def test_existing_download_never_deleted(
    catalog: Dataset, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    response(monkeypatch, CSV)
    target = tmp_path / "existing.csv"
    target.write_bytes(b"preserve")
    with pytest.raises(FileExistsError):
        download(catalog.sources[0], target, None)
    assert target.read_bytes() == b"preserve"


def test_pytrace_xml_error_is_never_an_archive(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    response(monkeypatch, b"<?xml version='1.0'?><Error>NoSuchBucket</Error>")
    target = tmp_path / "pytracebugs_dataset_v1.rar"
    source = Source(filename=target.name, url=PYTRACE_ARCHIVE)
    with pytest.raises(ValueError, match="Expected RAR5"):
        download(source, target, None)
    assert not target.exists()


def test_large_archive_exception_is_limited_to_pinned_pytrace_capture() -> None:
    with pytest.raises(ValidationError, match="approved source size"):
        Artifact(
            filename="other.rar",
            url="https://zenodo.org/other.rar",
            sha256="0" * 64,
            size_bytes=MAX_BYTES + 1,
        )
    artifact = Artifact(
        filename="pytracebugs_dataset_v1.rar",
        url=PYTRACE_ARCHIVE,
        sha256="0" * 64,
        size_bytes=PYTRACE_ARCHIVE_BYTES,
    )
    assert artifact.size_bytes == PYTRACE_ARCHIVE_BYTES


@pytest.mark.parametrize(
    "filename,link", [("../escape", False), ("/escape", False), ("link", True)]
)
def test_shared_safe_extraction_rejects_hostile_archives(
    filename: str,
    link: bool,
    catalog: Dataset,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    catalog.sources[0].extract_zip = True
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        entry = zipfile.ZipInfo(filename)
        if link:
            entry.create_system = 3
            entry.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(entry, b"inert")
    response(monkeypatch, output.getvalue())
    from app.core.errors import APIError

    with pytest.raises(APIError):
        acquire(catalog.dataset_id, tmp_path)
    assert not list(tmp_path.rglob("fixture.csv"))
    assert not list(tmp_path.rglob("*.json"))


def test_manifest_rejects_unknown_source_and_symlinks(
    catalog: Dataset, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    response(monkeypatch, CSV)
    manifest = acquire(catalog.dataset_id, tmp_path)
    path = tmp_path / "manifests" / f"{catalog.dataset_id}.json"
    data = json.loads(path.read_text())
    data["artifacts"][0]["url"] = "https://unapproved.example/data"
    path.write_text(json.dumps(data))
    with pytest.raises(ValidationError):
        read_manifest(path)
    root = tmp_path / "raw" / "java" / catalog.dataset_id
    (root / "unexpected").symlink_to(tmp_path / "manifests")
    with pytest.raises(ValueError, match="symlink"):
        verify(root, manifest)
    with pytest.raises(ValueError, match="Unknown dataset"):
        acquire("typescript_unapproved", tmp_path)


def test_descriptive_csv_audit_preserves_duplicate_columns(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_bytes(CSV + b"project,1,B,3,2\nproject,1,C,?,bad\nmalformed\n")
    result = csv_profile(path)
    assert result["raw_columns"] == ["name", "version", "name", "wmc", "bug"]
    assert result["rows"] == 4 and result["malformed_rows"] == 1
    assert result["duplicate_rows_exact"] == 1
    assert result["missing_by_column_index_and_name"]["3:wmc"] == 1
    assert result["labels"]["zero"] == 1
    assert result["labels"]["positive"] == 2
    assert result["labels"]["invalid"] == 1
    assert result["identity_column_index"] == 2


def test_all_tracked_manifests_validate_without_network() -> None:
    catalog = sources()
    paths = sorted((DATA / "manifests").glob("*.json"))
    assert {path.stem for path in paths} == set(catalog)
    for path in paths:
        manifest = read_manifest(path)
        assert manifest.acquired_at.tzinfo is not None
        assert manifest.artifacts


def test_pytracebugs_manifest_and_profile_contents() -> None:
    manifest = read_manifest(
        DATA / "manifests" / "python_pytracebugs_89a09db9add3.json"
    )
    assert manifest.dataset.canonical_name == "PyTraceBugs"
    assert manifest.dataset.acquisition_status == "ACQUIRED"
    assert manifest.dataset.blocker is None
    assert len(manifest.artifacts) == 5
    assert {a.filename for a in manifest.artifacts} == {
        "README.md",
        "LICENSE",
        "pytracebugs_dataset_v1.rar",
        "archive-capture.json",
        "author-paper.tex",
    }
    assert manifest.profile.get("archive_format") == "RAR5"
    assert manifest.profile.get("entries") == 47172
    assert manifest.profile.get("files") == 47169


def test_bug_metadata_remains_inert_and_abbreviations_are_not_full_pins(
    tmp_path: Path,
) -> None:
    bug = tmp_path / "extracted" / f"BugsInPy-{BUGSINPY}" / "projects/p/bugs/1"
    bug.mkdir(parents=True)
    (bug / "bug.info").write_text(
        'buggy_commit_id="abcdef1"\nfixed_commit_id="' + "a" * 40 + '"\n'
        'test_file="$(touch should-never-exist)"\n'
    )
    (bug / "bug_patch.txt").write_text("+++ b/module.py\n")
    result = bugsinpy_profile(tmp_path)
    assert result["bug_instances"] == 1
    assert result["invalid_or_missing_revision_pairs"] == 0
    assert result["pairs_with_abbreviated_unresolved_revisions"] == 1
    assert result["instances"][0]["patch_paths"] == ["module.py"]
    assert result["instances"][0]["test_file"] == "$(touch should-never-exist)"
    assert not Path("should-never-exist").exists()
    assert result["direct_function_labels"] is False
    assert result["class_balance"] is None


def test_javascript_audit_distinguishes_refs_from_buggy_parents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.dataset_audit.JS_PROJECTS", {"Bower": "bower"})
    (tmp_path / "Projects__Bower__Bower_bugs.csv").write_text(
        "ID;Number of tests\n1;2\n"
    )
    (tmp_path / "Bower-refs.json").write_text(
        json.dumps(
            [{"ref": "refs/tags/Bug-1", "object": {"type": "tag", "sha": "a" * 40}}]
        )
    )
    with zipfile.ZipFile(tmp_path / "Projects__Bower__Bower-1.zip", "w") as archive:
        archive.writestr("buggy/inert.zip", b"not opened or executed")
    result = bugsjs_profile(tmp_path)
    assert result["bug_instances"] == 1
    assert result["revision_refs"]["Bower"][0]["object_type"] == "tag"
    assert result["missing_expected_bug_tags"] == [
        "Bower:refs/tags/Bug-1-full",
        "Bower:refs/tags/Bug-1-test",
    ]
    assert "parent of Bug-ID" in result["buggy_revision_rule"]
    assert result["direct_file_labels"] is False
    assert result["class_balance"] is None
    assert not (tmp_path / "buggy").exists()
