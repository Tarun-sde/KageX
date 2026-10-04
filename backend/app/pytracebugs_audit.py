"""Bounded, read-only RAR5 inspection using the host's existing libarchive.

Never extracts to disk or deserializes pickle. Only tiny Python text samples are
read into memory for syntax inspection, never imported or executed.
"""

import ast
import ctypes
import ctypes.util
import hashlib
import json
import resource
import stat
import sys
import textwrap
import time
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

from app.dataset_sources import (
    PYTRACE_ARCHIVE,
    PYTRACE_CAPTURE,
    PYTRACE_CDX_SHA1,
    PYTRACE_ORIGINAL,
)


def inspect_archive(path: Path) -> dict[str, Any]:
    library_path = ctypes.util.find_library("archive")
    if library_path is None:
        raise ValueError(
            "RAR inspection requires an existing system libarchive; "
            "do not install benchmark dependencies"
        )
    library = ctypes.CDLL(library_path)
    pointer = ctypes.c_void_p
    signatures = {
        "archive_read_new": ([], pointer),
        "archive_read_support_format_rar5": ([pointer], ctypes.c_int),
        "archive_read_open_filename": (
            [pointer, ctypes.c_char_p, ctypes.c_size_t],
            ctypes.c_int,
        ),
        "archive_read_next_header": ([pointer, ctypes.POINTER(pointer)], ctypes.c_int),
        "archive_entry_pathname": ([pointer], ctypes.c_char_p),
        "archive_entry_size": ([pointer], ctypes.c_int64),
        "archive_entry_filetype": ([pointer], ctypes.c_uint),
        "archive_entry_symlink": ([pointer], ctypes.c_char_p),
        "archive_entry_hardlink": ([pointer], ctypes.c_char_p),
        "archive_entry_is_encrypted": ([pointer], ctypes.c_int),
        "archive_read_data": ([pointer, pointer, ctypes.c_size_t], ctypes.c_ssize_t),
        "archive_read_free": ([pointer], ctypes.c_int),
        "archive_error_string": ([pointer], ctypes.c_char_p),
        "archive_version_string": ([], ctypes.c_char_p),
    }
    for name, (arguments, result) in signatures.items():
        function = getattr(library, name)
        function.argtypes = arguments
        function.restype = result
    archive = library.archive_read_new()
    if not archive:
        raise ValueError("Could not allocate archive reader")
    deadline = time.monotonic() + 600
    groups: Counter[str] = Counter()
    tables: list[dict[str, Any]] = []
    samples: dict[str, Any] = {}
    entries = files = directories = total_bytes = 0
    try:
        if library.archive_read_support_format_rar5(archive) != 0:
            raise ValueError("RAR5 support unavailable in existing libarchive")
        if library.archive_read_open_filename(archive, str(path).encode(), 65536) != 0:
            raise ValueError("Unable to open RAR5 payload")
        entry = pointer()
        while True:
            status = library.archive_read_next_header(archive, ctypes.byref(entry))
            if status == 1:  # ARCHIVE_EOF
                break
            if status != 0:
                error = library.archive_error_string(archive)
                raise ValueError(f"Invalid/incomplete RAR: {error!r}")
            entries += 1
            if entries > 10000000 or time.monotonic() > deadline:
                raise ValueError("RAR inventory resource limit")
            name = library.archive_entry_pathname(entry).decode(
                "utf-8", errors="strict"
            )
            member = PurePosixPath(name)
            if (
                len(name) > 4096
                or not member.parts
                or member.is_absolute()
                or ".." in member.parts
                or "\\" in name
                or ":" in name
            ):
                raise ValueError("Unsafe RAR member path")
            kind = library.archive_entry_filetype(entry)
            if (
                kind not in {stat.S_IFDIR, stat.S_IFREG}
                or library.archive_entry_symlink(entry)
                or library.archive_entry_hardlink(entry)
                or library.archive_entry_is_encrypted(entry) > 0
            ):
                raise ValueError("Links/special/encrypted files are not admitted")
            if kind == stat.S_IFDIR:
                directories += 1
                continue
            size = library.archive_entry_size(entry)
            total_bytes += size
            if size < 0 or total_bytes > 128 * 1024**3:
                raise ValueError("RAR declared expansion limit")
            files += 1
            group = (
                "/".join(member.parts[:2]) if len(member.parts) > 2 else member.parts[0]
            )
            groups[group] += 1
            if len(groups) > 1000:
                raise ValueError("Unexpected archive directory structure")
            if member.suffix in {".pickle", ".pkl"}:
                if len(tables) >= 100:
                    raise ValueError("Unexpected metadata table count")
                tables.append({"path": name, "size_bytes": size, "deserialized": False})
            # Inspect tiny buggy/fixed/stable examples, at most four in total.
            sample_key = group
            for suffix in ("before_merge.py", "after_merge.py"):
                if name.endswith(suffix):
                    sample_key += "/" + suffix
            if (
                member.suffix == ".py"
                and "snippet" in group
                and sample_key not in samples
                and len(samples) < 4
                and 0 < size <= 262144
            ):
                buffer = ctypes.create_string_buffer(size + 1)
                count = library.archive_read_data(archive, buffer, size + 1)
                if count != size:
                    raise ValueError(
                        "Unexpected source sample size or decompression error"
                    )
                source = buffer.raw[:count]
                try:
                    tree = ast.parse(textwrap.dedent(source.decode("utf-8-sig")))
                    function_present = any(
                        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                        for node in ast.walk(tree)
                    )
                    syntax = "parsed_as_text_only"
                except (SyntaxError, UnicodeError):  # fmt: skip
                    function_present = None
                    syntax = "not_parseable_with_current_python"
                samples[sample_key] = {
                    "path": name,
                    "size_bytes": size,
                    "sha256": hashlib.sha256(source).hexdigest(),
                    "function_or_method_definition_present": function_present,
                    "syntax_check": syntax,
                }
        if not {"buggy_dataset", "stable_dataset"}.issubset(
            {g.split("/")[0] for g in groups}
        ):
            raise ValueError("Expected buggy/stable collections are absent")
        return {
            "archive_provenance": {
                "original_url": PYTRACE_ORIGINAL,
                "replacement_url": PYTRACE_ARCHIVE,
                "capture_timestamp_utc": PYTRACE_CAPTURE,
                "archival_payload_sha1": PYTRACE_CDX_SHA1,
                "original_host_status": "HTTP 404 application/xml NoSuchBucket",
                "preservation_evidence": (
                    "archive-capture.json; exact official URL, HTTP 200 RAR capture, "
                    "independently checked payload digest"
                ),
            },
            "archive_format": "RAR5",
            "inventory_tool": library.archive_version_string().decode(),
            "entries": entries,
            "files": files,
            "directories": directories,
            "declared_uncompressed_bytes": total_bytes,
            "files_by_directory_group": dict(sorted(groups.items())),
            "opaque_pickle_tables": tables,
            "inert_python_samples": samples,
            "records": None,
            "missingness": None,
            "duplicates": None,
            "class_balance": None,
            "limitation": (
                "File counts are not supervised row counts. Pickle tables were not "
                "deserialized; labels, table contents and the full source population "
                "remain unvalidated. No archive contents were written to disk."
            ),
        }
    finally:
        library.archive_read_free(archive)


if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_AS, (1536 * 1024**2, 1536 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (600, 600))
    print(json.dumps(inspect_archive(Path(sys.argv[1])), allow_nan=False))
