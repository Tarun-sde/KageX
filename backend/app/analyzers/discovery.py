"""Copy only bounded regular source files into a private per-run workspace."""

import os
import stat
import time
from pathlib import Path

from app.analyzers.contracts import EXTENSIONS, AnalysisFailure, Language
from app.core.config import Settings


def check_time(deadline: float) -> None:
    if time.monotonic() >= deadline:
        raise AnalysisFailure(
            "ANALYZER_TIMEOUT", "Static analysis exceeded its time limit."
        )


def discover(
    source: Path, target: Path, settings: Settings, deadline: float
) -> tuple[dict[Language, list[str]], int, list[dict[str, str]]]:
    if source.is_symlink() or not source.is_dir():
        raise AnalysisFailure("SOURCE_UNAVAILABLE", "Prepared source is unavailable.")
    grouped: dict[Language, list[str]] = {}
    warnings: list[dict[str, str]] = []
    entries = size = unsupported = 0
    target.mkdir(mode=0o700)
    # fwalk plus dir_fd/O_NOFOLLOW avoids following links during reads, including
    # a file being replaced between directory enumeration and open.
    for directory, dirs, files, descriptor in os.fwalk(source, follow_symlinks=False):
        check_time(deadline)
        dirs.sort()
        relative_dir = Path(directory).relative_to(source)
        if len(relative_dir.parts) > 32:
            raise AnalysisFailure(
                "SOURCE_LIMIT_EXCEEDED", "Source nesting exceeds the limit."
            )
        for name in sorted(dirs + files):
            entries += 1
            if entries > settings.max_archive_files:
                raise AnalysisFailure(
                    "SOURCE_LIMIT_EXCEEDED", "Source entry count exceeds the limit."
                )
            relative = (relative_dir / name).as_posix()
            info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode) or not (
                stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)
            ):
                raise AnalysisFailure(
                    "UNSAFE_SOURCE", "Source contains a link or special file."
                )
            if stat.S_ISDIR(info.st_mode):
                continue
            size += info.st_size
            if size > settings.max_extracted_size_mb * 1048576:
                raise AnalysisFailure(
                    "SOURCE_LIMIT_EXCEEDED", "Source size exceeds the limit."
                )
            language = EXTENSIONS.get(Path(name).suffix.lower())
            if language is None:
                unsupported += 1
                continue
            if info.st_size > settings.max_analysis_file_bytes:
                warnings.append({"code": "FILE_TOO_LARGE", "relative_path": relative})
                continue
            fd = os.open(
                name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor
            )
            with os.fdopen(fd, "rb") as stream:
                opened = os.fstat(stream.fileno())
                if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
                    raise AnalysisFailure(
                        "UNSAFE_SOURCE", "Source contains an unsafe file."
                    )
                data = stream.read(settings.max_analysis_file_bytes + 1)
            if len(data) > settings.max_analysis_file_bytes:
                raise AnalysisFailure(
                    "SOURCE_LIMIT_EXCEEDED", "Source file exceeds the limit."
                )
            if b"\x00" in data:
                warnings.append(
                    {"code": "BINARY_SOURCE_SKIPPED", "relative_path": relative}
                )
                continue
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            destination.write_bytes(data)
            destination.chmod(0o600)
            grouped.setdefault(language, []).append(relative)
    return grouped, unsupported, warnings
