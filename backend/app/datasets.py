"""Offline-first Phase 4A acquisition/verification. Never import benchmark code."""

import argparse
import hashlib
import json
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, SecretStr, model_validator

from app.core.config import Settings
from app.dataset_sources import (
    PYTRACE_ARCHIVE,
    PYTRACE_ARCHIVE_BYTES,
    Dataset,
    Source,
    sources,
)
from app.services.storage import extract_archive

DATA = Path(__file__).resolve().parents[2] / "data"
MAX_BYTES = 100 * 1048576


def archive_limits() -> Settings:
    # The shared extractor needs validated settings, but never connects to services.
    return Settings(
        _env_file=None,
        app_env="test",
        database_url=SecretStr("postgresql+psycopg://unused:unused@localhost/unused"),
        redis_url=SecretStr("redis://localhost/15"),
        max_upload_size_mb=100,
        max_extracted_size_mb=1000,
        max_archive_files=10000,
        max_file_size_mb=100,
    )


class Artifact(Source):
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0, le=PYTRACE_ARCHIVE_BYTES)

    @model_validator(mode="after")
    def bounded_size(self) -> Artifact:
        limit = PYTRACE_ARCHIVE_BYTES if self.url == PYTRACE_ARCHIVE else MAX_BYTES
        if self.size_bytes > limit:
            raise ValueError("Artifact exceeds its approved source size limit")
        return self


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    manifest_version: Literal[1] = 1
    dataset: Dataset
    acquired_at: datetime
    checksum_provenance: str
    artifacts: list[Artifact]
    extracted_files: dict[str, str]
    profile: dict[str, JsonValue]


def checksum(path: Path, algorithm: str = "sha256") -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()


def read_manifest(path: Path) -> Manifest:
    if path.is_symlink() or path.stat().st_size > 8 * 1048576:
        raise ValueError("Unsafe or oversized manifest")
    manifest = Manifest.model_validate_json(path.read_bytes())
    approved = sources().get(manifest.dataset.dataset_id)
    if approved is None or manifest.dataset != approved:
        raise ValueError("Manifest does not match the approved dataset catalog")
    if [
        Source.model_validate(a.model_dump(include=set(Source.model_fields)))
        for a in manifest.artifacts
    ] != approved.sources:
        raise ValueError("Manifest artifact list does not match approved sources")
    for name, digest in manifest.extracted_files.items():
        parts = Path(name).parts
        if (
            not parts
            or Path(name).is_absolute()
            or ".." in parts
            or "\\" in name
            or len(digest) != 64
            or any(c not in "0123456789abcdef" for c in digest)
        ):
            raise ValueError("Invalid extracted-file checksum entry")
    return manifest


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: object,
        code: int,
        msg: str,
        headers: object,
        newurl: str,
    ) -> None:
        raise ValueError("Dataset redirects are not followed; review the approved URL")


def download(source: Source, target: Path, expected: Artifact | None) -> Artifact:
    # Fixed HTTPS sources, no environment proxy or credentials, no shell/client hooks.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(
        source.url,
        headers={"User-Agent": "KageX-Phase4A-audit", "Accept-Encoding": "identity"},
    )
    is_pytrace_archive = source.url == PYTRACE_ARCHIVE
    limit = PYTRACE_ARCHIVE_BYTES if is_pytrace_archive else MAX_BYTES
    deadline = time.monotonic() + (3600 if is_pytrace_archive else 120)
    total = 0
    created = False
    try:
        with (
            opener.open(request, timeout=60 if is_pytrace_archive else 20) as response,
            target.open("xb") as output,
        ):
            created = True
            advertised = response.headers.get("Content-Length")
            if advertised and int(advertised) > limit:
                raise ValueError("Artifact exceeds its approved download limit")
            while block := response.read(65536):
                if (
                    is_pytrace_archive
                    and total == 0
                    and not block.startswith(b"Rar!\x1a\x07\x01\x00")
                ):
                    raise ValueError("Expected RAR5 archive, not an error page")
                total += len(block)
                if total > limit or time.monotonic() > deadline:
                    raise ValueError("Dataset download resource limit exceeded")
                output.write(block)
            if advertised and total != int(advertised):
                raise ValueError("Incomplete dataset download")
            if is_pytrace_archive and total != PYTRACE_ARCHIVE_BYTES:
                raise ValueError("Incomplete PyTraceBugs archival payload")
        digest = checksum(target)
        if expected and (digest != expected.sha256 or total != expected.size_bytes):
            raise ValueError(
                "Dataset checksum mismatch; existing manifest is not overwritten"
            )
        if source.upstream_md5 and checksum(target, "md5") != source.upstream_md5:
            raise ValueError("Upstream archival checksum mismatch")
        if source.upstream_sha1 and checksum(target, "sha1") != source.upstream_sha1:
            raise ValueError("Archival payload SHA-1 mismatch")
        return Artifact(**source.model_dump(), sha256=digest, size_bytes=total)
    except BaseException:
        if created:
            target.unlink(missing_ok=True)
        raise


def file_inventory(root: Path) -> dict[str, str]:
    inventory: dict[str, str] = {}
    if not root.exists():
        return inventory
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Dataset tree contains a symlink")
        if path.is_file():
            if path.stat().st_nlink != 1:
                raise ValueError("Dataset tree contains a hard link")
            inventory[path.relative_to(root).as_posix()] = checksum(path)
        elif not path.is_dir():
            raise ValueError("Dataset tree contains a special file")
    return inventory


def verify(root: Path, manifest: Manifest) -> None:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Missing or unsafe dataset directory")
    expected = {a.filename: a.sha256 for a in manifest.artifacts}
    expected.update(
        {
            f"extracted/{name}": digest
            for name, digest in manifest.extracted_files.items()
        }
    )
    if file_inventory(root) != expected:
        raise ValueError("Dataset files differ from manifest; refusing to overwrite")
    for artifact in manifest.artifacts:
        if (root / artifact.filename).stat().st_size != artifact.size_bytes:
            raise ValueError("Artifact size differs from manifest")


def acquire(identifier: str, data: Path = DATA) -> Manifest:
    dataset = sources().get(identifier)
    if dataset is None:
        raise ValueError(f"Unknown dataset identifier: {identifier}")
    target = data / "raw" / dataset.language / identifier
    manifest_path = data / "manifests" / f"{identifier}.json"
    manifest = read_manifest(manifest_path) if manifest_path.exists() else None
    if target.parent.resolve() != target.parent.absolute():
        raise ValueError("Dataset parents must not contain symlinks")
    # Refuse user-modified or partial directories rather than silently redownloading.
    if target.exists() or target.is_symlink():
        if manifest is None:
            raise ValueError("Existing dataset lacks a manifest; review it manually")
        verify(target, manifest)
        return manifest
    target.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".acquire-", dir=target.parent) as temporary:
        staging = Path(temporary) / "dataset"
        staging.mkdir(mode=0o700)
        artifacts = []
        for index, source in enumerate(dataset.sources):
            expected = manifest.artifacts[index] if manifest else None
            artifact = download(source, staging / source.filename, expected)
            artifacts.append(artifact)
            if source.extract_zip:
                # Reuse the Phase 2 traversal/link/bomb/CRC defenses, unchanged.
                extract_archive(
                    staging / source.filename,
                    staging / "extracted",
                    archive_limits(),
                    time.monotonic() + 120,
                )
        if manifest:
            verify(staging, manifest)
        else:
            from app.dataset_audit import profile

            manifest = Manifest(
                dataset=dataset,
                acquired_at=datetime.now(UTC),
                artifacts=artifacts,
                checksum_provenance=(
                    "SHA-256 measured on initial approved-source acquisition; GitHub "
                    "URLs pin commits where possible. Zenodo CSV MD5 additionally "
                    "verified against archival metadata. Subsequent acquisition must "
                    "match this manifest exactly."
                ),
                extracted_files=file_inventory(staging / "extracted"),
                profile=profile(staging, dataset),
            )
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        if not manifest_path.exists():
            # Exclusive creation prevents concurrent jobs overwriting provenance.
            with manifest_path.open("x", encoding="utf-8") as output:
                output.write(manifest.model_dump_json(indent=2) + "\n")
        staging.rename(target)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["list", "acquire", "verify", "audit"])
    parser.add_argument("dataset", nargs="?", help="Exact approved ID, or all")
    args = parser.parse_args()
    catalog = sources()
    if args.action == "list":
        for key, dataset in catalog.items():
            print(key, dataset.acquisition_status)
        return
    identifiers = list(catalog) if args.dataset == "all" else [args.dataset]
    for identifier in identifiers:
        if identifier not in catalog:
            parser.error("Use an approved identifier from list, or all")
        if args.action == "acquire":
            manifest = acquire(identifier)
        else:
            manifest = read_manifest(DATA / "manifests" / f"{identifier}.json")
            root = DATA / "raw" / manifest.dataset.language / identifier
            verify(root, manifest)
            if args.action == "audit":
                from app.dataset_audit import profile

                print(
                    json.dumps(
                        profile(root, manifest.dataset), indent=2, allow_nan=False
                    )
                )
        print(identifier, manifest.dataset.acquisition_status, "verified")


if __name__ == "__main__":
    main()
