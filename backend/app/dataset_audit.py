"""Descriptive audits of inert bytes. No labels/features/splits are constructed."""

import csv
import json
import math
import re
import statistics
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

from app.dataset_sources import BUGSINPY, JS_PROJECTS, Dataset
from app.datasets import archive_limits
from app.services.storage import preflight_zip


def csv_profile(path: Path, delimiter: str = ",") -> dict[str, Any]:
    csv.field_size_limit(1048576)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, delimiter=delimiter, strict=True)
        header = next(reader)
        rows = []
        malformed = 0
        for row in reader:
            if len(row) != len(header):
                malformed += 1
            else:
                rows.append(row)
            if len(rows) + malformed > 250000:
                raise ValueError("CSV audit row limit exceeded")
    columns = [column.strip() for column in header]
    missing: dict[str, int] = {}
    numeric: dict[str, Any] = {}
    for index, name in enumerate(columns):
        key = f"{index}:{name}"  # Duplicate column names are retained, not overwritten.
        values = [row[index].strip() for row in rows]
        absent = {"", "?", "NA", "N/A", "NaN", "null"}
        missing[key] = sum(value in absent for value in values)
        numbers = []
        invalid = 0
        for value in values:
            if value in absent:
                continue
            try:
                number = float(value)
                if not math.isfinite(number):
                    invalid += 1
                else:
                    numbers.append(number)
            except ValueError:
                invalid += 1
        if numbers:
            numeric[key] = {
                "valid": len(numbers),
                "invalid_nonmissing": invalid,
                "min": min(numbers),
                "max": max(numbers),
                "median": statistics.median(numbers),
            }
    identity = (
        columns.index("classname")
        if "classname" in columns
        else (
            max(index for index, name in enumerate(columns) if name == "name")
            if "name" in columns
            else (columns.index("ID") if "ID" in columns else None)
        )
    )
    identities = [row[identity].strip() for row in rows] if identity is not None else []
    label = "bug" if "bug" in columns else ("bugs" if "bugs" in columns else None)
    balance: dict[str, Any] | None = None
    if label:
        values = [row[columns.index(label)].strip() for row in rows]
        zero = positive = invalid = 0
        for value in values:
            try:
                count = float(value)
                if not math.isfinite(count) or count < 0 or not count.is_integer():
                    invalid += 1
                elif count == 0:
                    zero += 1
                else:
                    positive += 1
            except ValueError:
                invalid += 1
        balance = {
            "field": label,
            "raw_distribution": dict(sorted(Counter(values).items())),
            "zero": zero,
            "positive": positive,
            "invalid": invalid,
            "positive_fraction_valid": positive / (positive + zero)
            if positive + zero
            else None,
        }
    return {
        "raw_columns": header,
        "columns_trimmed_for_audit_only": columns,
        "rows": len(rows),
        "malformed_rows": malformed,
        "duplicate_rows_exact": len(rows) - len({tuple(row) for row in rows}),
        "duplicate_column_names": [
            name for name, count in Counter(columns).items() if count > 1
        ],
        "missing_by_column_index_and_name": missing,
        "numeric_summary": numeric,
        "identity_column_index": identity,
        "unique_identities": len(set(identities)),
        "duplicate_identities": len(identities) - len(set(identities)),
        "missing_identities": identities.count(""),
        "labels": balance,
        "project_versions": [
            {"project": project, "version": version}
            for project, version in sorted(
                {
                    (row[columns.index("name")], row[columns.index("version")])
                    for row in rows
                }
            )
        ]
        if "name" in columns and "version" in columns
        else None,
    }


def key_values(path: Path) -> dict[str, str]:
    # Shell-looking files are read as strings; never source/eval/execute them.
    return {
        key.strip(): value.strip().strip('"')
        for line in path.read_text().splitlines()
        if "=" in line
        for key, value in [line.split("=", 1)]
    }


def bugsinpy_profile(root: Path) -> dict[str, Any]:
    projects = root / "extracted" / f"BugsInPy-{BUGSINPY}" / "projects"
    instances = []
    fields: set[str] = set()
    invalid_revisions = abbreviated_revisions = missing_patches = 0
    for info in sorted(projects.glob("*/bugs/*/bug.info")):
        values = key_values(info)
        fields.update(values)
        buggy, fixed = values.get("buggy_commit_id"), values.get("fixed_commit_id")
        invalid_revisions += int(
            any(
                not re.fullmatch(r"[0-9a-f]{7,40}", value or "")
                for value in [buggy, fixed]
            )
        )
        abbreviated_revisions += int(
            any(
                re.fullmatch(r"[0-9a-f]{7,39}", value or "") for value in [buggy, fixed]
            )
        )
        patch = info.with_name("bug_patch.txt")
        missing_patches += int(not patch.exists())
        text = patch.read_text(errors="replace") if patch.exists() else ""
        paths = sorted(
            set(re.findall(r"^(?:\+\+\+ b/|--- a/)(.+)$", text, re.MULTILINE))
        )
        instances.append(
            {
                "project": info.parents[2].name,
                "bug_id": info.parent.name,
                "buggy_commit": buggy,
                "fixed_commit": fixed,
                "test_file": values.get("test_file"),
                "patch_paths": paths,
            }
        )
    pairs = [
        (bug["project"], bug["buggy_commit"], bug["fixed_commit"]) for bug in instances
    ]
    return {
        "bug_instances": len(instances),
        "project_counts": dict(
            sorted(Counter(str(bug["project"]) for bug in instances).items())
        ),
        "project_metadata": {
            path.parent.name: key_values(path)
            for path in sorted(projects.glob("*/project.info"))
        },
        "metadata_fields": sorted(fields),
        "invalid_or_missing_revision_pairs": invalid_revisions,
        "pairs_with_abbreviated_unresolved_revisions": abbreviated_revisions,
        "missing_patches": missing_patches,
        "patches_without_recognized_paths": sum(
            not bug["patch_paths"] for bug in instances
        ),
        "duplicate_project_revision_pairs": len(pairs) - len(set(pairs)),
        "identical_buggy_and_fixed_revisions": sum(
            bug["buggy_commit"] == bug["fixed_commit"] for bug in instances
        ),
        "direct_function_labels": False,
        "negative_function_samples": None,
        "available_static_feature_columns": [],
        "class_balance": None,
        "instances": instances,
    }


def bugsjs_profile(root: Path) -> dict[str, Any]:
    tables = {
        project: csv_profile(root / f"Projects__{project}__{project}_bugs.csv", ";")
        for project in JS_PROJECTS
    }
    revisions: dict[str, Any] = {}
    missing_tags = []
    for project in JS_PROJECTS:
        refs = json.loads((root / f"{project}-refs.json").read_text())
        revisions[project] = [
            {
                "ref": ref["ref"],
                "object_type": ref["object"]["type"],
                "sha": ref["object"]["sha"],
            }
            for ref in refs
        ]
        names = {ref["ref"] for ref in refs}
        with (root / f"Projects__{project}__{project}_bugs.csv").open() as stream:
            for row in csv.DictReader(stream, delimiter=";"):
                for suffix in ["", "-full", "-test"]:
                    tag = f"refs/tags/Bug-{row['ID']}{suffix}"
                    if tag not in names:
                        missing_tags.append(f"{project}:{tag}")
    # Inspect one archive's directory only; do not recursively unpack its content.
    preflight_zip(root / "Projects__Bower__Bower-1.zip", archive_limits())
    with zipfile.ZipFile(root / "Projects__Bower__Bower-1.zip") as archive:
        members = [
            {"name": item.filename, "size_bytes": item.file_size}
            for item in archive.infolist()
        ]
    return {
        "project_counts": {project: table["rows"] for project, table in tables.items()},
        "bug_instances": sum(table["rows"] for table in tables.values()),
        "bug_tables": tables,
        "revision_refs": revisions,
        "missing_expected_bug_tags": missing_tags,
        "buggy_revision_rule": (
            "Upstream myGit.py uses parent of Bug-ID; fixed uses Bug-ID-full; "
            "test-only uses Bug-ID-test. Tag object SHAs are inventoried, but "
            "buggy parent commits and changed source files are not acquired."
        ),
        "sample_archive_members": members,
        "direct_file_labels": False,
        "negative_file_samples": None,
        "class_balance": None,
        "phase3_static_features_directly_available": False,
    }


def profile(root: Path, dataset: Dataset) -> dict[str, Any]:
    if dataset.language == "java":
        delimiter = ";" if "dambros" in dataset.dataset_id else ","
        tables = {
            path.name: csv_profile(path, delimiter)
            for path in sorted(root.glob("*.csv"))
        }
        if not tables or any(table["labels"] is None for table in tables.values()):
            raise ValueError("Expected approved Java tables and defect count fields")
        return {
            "tables": tables,
            "total_rows": sum(table["rows"] for table in tables.values()),
            "table_count": len(tables),
            "project_inventory": {
                filename: table["project_versions"]
                or [{"project": Path(filename).stem, "version": None}]
                for filename, table in tables.items()
            },
            "class_level_evidence": (
                "Upstream documentation plus class identifiers; metric "
                "compatibility is unvalidated."
            ),
        }
    if "bugsinpy" in dataset.dataset_id:
        return bugsinpy_profile(root)
    if dataset.language == "javascript":
        return bugsjs_profile(root)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.pytracebugs_audit",
            str(root / "pytracebugs_dataset_v1.rar"),
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
        timeout=610,
    )
    return dict(json.loads(result.stdout))
