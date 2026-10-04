"""Confined, inert local source storage. No extraction APIs or source execution."""

import logging
import shutil
import stat
import struct
import time
import zipfile
import zlib
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from uuid import UUID

from app.core.config import Settings
from app.core.errors import APIError

logger = logging.getLogger(__name__)
MIB = 1024 * 1024


class Storage:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.root = settings.project_storage_root.resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def path(self, identifier: UUID | str) -> Path:
        path = self.root / str(identifier)
        if path.is_symlink() or not path.resolve().is_relative_to(self.root):
            raise APIError(503, "STORAGE_UNAVAILABLE", "Source storage is unavailable.")
        return path

    @contextmanager
    def staging(self) -> Iterator[Path]:
        staging_root = self.path(".staging")
        staging_root.mkdir(exist_ok=True, mode=0o700)
        with TemporaryDirectory(dir=staging_root) as directory:
            yield Path(directory)

    def publish(self, source: Path, project_id: UUID) -> None:
        destination = self.path(project_id)
        if destination.exists():
            raise APIError(
                409, "SOURCE_EXISTS", "This project already has stored source."
            )
        source.rename(destination)

    def remove(self, project_id: UUID) -> None:
        path = self.path(project_id)
        if path.exists():
            shutil.rmtree(path)

    @contextmanager
    def deleting(self, project_id: UUID) -> Iterator[None]:
        """Quarantine before DB deletion; restore on rollback; purge after commit."""
        source = self.path(project_id)
        trash_root = self.path(".trash")
        trash_root.mkdir(exist_ok=True, mode=0o700)
        trash = trash_root / str(project_id)
        if trash.exists() or trash.is_symlink():
            raise APIError(
                503, "STORAGE_UNAVAILABLE", "Source cleanup requires attention."
            )
        moved = source.exists()
        if moved:
            source.rename(trash)
        try:
            yield
        except BaseException:
            if moved:
                trash.rename(source)
            raise
        else:
            if moved:
                try:
                    shutil.rmtree(trash)
                except OSError:
                    logger.error("Source trash cleanup failed project=%s", project_id)


def check_deadline(deadline: float) -> None:
    if time.monotonic() > deadline:
        raise APIError(
            408, "INGESTION_TIMEOUT", "Source preparation exceeded its time limit."
        )


def preflight_zip(archive: Path, settings: Settings) -> None:
    """Bound the central directory before ZipFile allocates all its entries."""
    size = archive.stat().st_size
    if size > settings.max_upload_size_mb * MIB:
        raise APIError(413, "UPLOAD_TOO_LARGE", "The archive exceeds the upload limit.")
    with archive.open("rb") as stream:
        stream.seek(max(0, size - 65557))
        tail = stream.read(65557)
    position = tail.rfind(b"PK\x05\x06")
    if position < 0 or len(tail) - position < 22:
        raise APIError(400, "INVALID_ARCHIVE", "Provide a valid ZIP archive.")
    _, disk, directory_disk, disk_entries, entries, directory_size, offset, comment = (
        struct.unpack_from("<4s4H2LH", tail, position)
    )
    if (
        disk
        or directory_disk
        or disk_entries != entries
        or entries == 65535
        or offset == 0xFFFFFFFF
        or directory_size == 0xFFFFFFFF
        or position + 22 + comment != len(tail)
        or offset + directory_size != size - (len(tail) - position)
    ):
        raise APIError(
            400,
            "INVALID_ARCHIVE",
            "Split, ZIP64, or malformed archives are unsupported.",
        )
    if entries > settings.max_archive_files:
        raise APIError(413, "TOO_MANY_FILES", "The archive has too many entries.")
    # Count central headers before ZipFile allocates ZipInfo objects. Do not trust
    # the EOCD entry count: a forged small count must not bypass the memory bound.
    with archive.open("rb") as stream:
        stream.seek(offset)
        end = offset + directory_size
        actual = 0
        while stream.tell() < end:
            header = stream.read(46)
            if len(header) != 46 or header[:4] != b"PK\x01\x02":
                raise APIError(400, "INVALID_ARCHIVE", "Invalid ZIP directory.")
            name_size, extra_size, comment_size = struct.unpack_from("<3H", header, 28)
            stream.seek(name_size + extra_size + comment_size, 1)
            actual += 1
            if actual > settings.max_archive_files:
                raise APIError(
                    413, "TOO_MANY_FILES", "The archive has too many entries."
                )
        if stream.tell() != end or actual != entries:
            raise APIError(400, "INVALID_ARCHIVE", "Invalid ZIP directory.")


def extract_archive(
    archive: Path, destination: Path, settings: Settings, deadline: float
) -> tuple[int, int]:
    preflight_zip(archive, settings)
    total = count = 0
    destination.mkdir(mode=0o700)
    try:
        with zipfile.ZipFile(archive) as zipped:
            entries = zipped.infolist()
            if len(entries) > settings.max_archive_files:
                raise APIError(
                    413, "TOO_MANY_FILES", "The archive has too many entries."
                )
            paths: dict[str, bool] = {}
            for entry in entries:
                check_deadline(deadline)
                raw = entry.orig_filename
                components = raw.rstrip("/").split("/")
                if (
                    not raw
                    or "\\" in raw
                    or ":" in raw
                    or any(
                        ord(character) < 32 or ord(character) == 127
                        for character in raw
                    )
                    or any(part in {"", ".", ".."} for part in components)
                    or len(raw.encode("utf-8")) > 512
                    or len(components) > 32
                    or PurePosixPath(raw).is_absolute()
                ):
                    raise APIError(
                        400,
                        "UNSAFE_ARCHIVE_PATH",
                        "The archive contains an unsafe path.",
                    )
                relative = PurePosixPath(*components)
                target = (destination / str(relative)).resolve()
                if not target.is_relative_to(destination.resolve()):
                    raise APIError(
                        400,
                        "UNSAFE_ARCHIVE_PATH",
                        "The archive contains an unsafe path.",
                    )
                key = str(relative).casefold()
                if key in paths or any(
                    paths.get(str(parent).casefold()) is False
                    for parent in relative.parents
                ):
                    raise APIError(
                        400,
                        "INVALID_ARCHIVE",
                        "The archive contains conflicting paths.",
                    )
                if not entry.is_dir() and any(
                    path.startswith(key + "/") for path in paths
                ):
                    raise APIError(
                        400,
                        "INVALID_ARCHIVE",
                        "The archive contains conflicting paths.",
                    )
                paths[key] = entry.is_dir()
                kind = stat.S_IFMT(entry.external_attr >> 16)
                if kind not in {0, stat.S_IFREG, stat.S_IFDIR} or (
                    kind == stat.S_IFDIR and not entry.is_dir()
                ):
                    raise APIError(
                        400,
                        "UNSAFE_ARCHIVE_ENTRY",
                        "Links and special files are not accepted.",
                    )
                if entry.flag_bits & 1 or entry.compress_type not in {
                    zipfile.ZIP_STORED,
                    zipfile.ZIP_DEFLATED,
                }:
                    raise APIError(
                        400,
                        "INVALID_ARCHIVE",
                        "Encrypted or unsupported compression is not accepted.",
                    )
                if entry.file_size > settings.max_file_size_mb * MIB:
                    raise APIError(
                        413,
                        "FILE_TOO_LARGE",
                        "An archived file exceeds the size limit.",
                    )
                total += entry.file_size
                if total > settings.max_extracted_size_mb * MIB:
                    raise APIError(
                        413,
                        "EXTRACTED_SIZE_LIMIT",
                        "The extracted source exceeds the size limit.",
                    )
                if (
                    entry.file_size / max(entry.compress_size, 1)
                    > settings.max_compression_ratio
                ):
                    raise APIError(
                        413,
                        "COMPRESSION_RATIO_LIMIT",
                        "The archive compression ratio exceeds the limit.",
                    )
            total = 0
            for entry in entries:
                check_deadline(deadline)
                target = destination / entry.filename
                if entry.is_dir():
                    target.mkdir(parents=True, exist_ok=True, mode=0o700)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                size = 0
                with zipped.open(entry) as source, target.open("xb") as output:
                    target.chmod(0o600)
                    while chunk := source.read(64 * 1024):
                        check_deadline(deadline)
                        size += len(chunk)
                        total += len(chunk)
                        if (
                            size > settings.max_file_size_mb * MIB
                            or total > settings.max_extracted_size_mb * MIB
                        ):
                            raise APIError(
                                413,
                                "EXTRACTED_SIZE_LIMIT",
                                "The extracted source exceeds the size limit.",
                            )
                        output.write(chunk)
                count += 1
            if not count:
                raise APIError(400, "INVALID_ARCHIVE", "The archive contains no files.")
    except (
        zipfile.BadZipFile,
        NotImplementedError,
        RuntimeError,
        EOFError,
        zlib.error,
    ) as error:
        raise APIError(
            400, "INVALID_ARCHIVE", "The ZIP archive is malformed or unsupported."
        ) from error
    return count, total
