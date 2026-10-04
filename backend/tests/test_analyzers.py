import json
import shutil
import sys
import time
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.analyzers.adapters import registry
from app.analyzers.contracts import AnalysisFailure, Language
from app.analyzers.discovery import discover
from app.analyzers.process import run_tool
from app.core.config import Settings

FIXTURES = Path(__file__).parent / "fixtures" / "analysis"


@pytest.fixture
def source(tmp_path: Path) -> Path:
    return Path(shutil.copytree(FIXTURES, tmp_path / "source"))


def test_python_metrics_identity_and_no_execution(
    source: Path, settings: Settings
) -> None:
    result = registry()["python"].analyze(
        source, ["python/sample.py"], settings, time.monotonic() + 20
    )
    assert not result.warnings
    by_name = {entity.qualified_name: entity for entity in result.entities}
    assert set(by_name) == {"choose", "Worker.choose", "Worker.choose.<locals>.nested"}
    choose = by_name["choose"]
    assert choose.entity_type == "function"
    assert choose.metrics["cyclomatic_complexity"] == 2
    assert choose.metrics["loc"] == 4
    assert choose.metrics["parameter_count"] == 2
    assert choose.metrics["branch_count"] == 1
    assert choose.metrics["halstead_volume"] > 0  # type: ignore[operator]
    assert choose.metric_schema_version == "python_function_v1"


def test_java_metrics_packages_and_nested_classes(
    source: Path, settings: Settings
) -> None:
    result = registry()["java"].analyze(
        source,
        ["java/alpha/Example.java", "java/beta/Example.java"],
        settings,
        time.monotonic() + 30,
    )
    assert not result.warnings
    by_name = {entity.qualified_name: entity for entity in result.entities}
    assert set(by_name) == {"alpha.Example", "alpha.Example$Nested", "beta.Example"}
    parent = by_name["alpha.Example"]
    assert parent.metrics["wmc"] == 2
    assert parent.metrics["noc"] == 1
    assert by_name["beta.Example"].metrics["dit"] == 2
    assert set(parent.metrics) == {
        "wmc",
        "dit",
        "noc",
        "cbo",
        "rfc",
        "lcom",
        "loc",
        "num_functions",
    }
    assert parent.start_line == 2


def test_javascript_fixed_configuration(
    source: Path, settings: Settings, tmp_path: Path
) -> None:
    marker = tmp_path / "EXECUTED"
    (source / "eslint.config.js").write_text(
        f"require('fs').writeFileSync({str(marker)!r}, 'bad');"
        "throw Error('bad config');"
    )
    (source / "package.json").write_text('{"scripts":{"install":"touch EXECUTED"}}')
    result = registry()["javascript"].analyze(
        source, ["script/sample.js"], settings, time.monotonic() + 20
    )
    assert not result.warnings
    assert not marker.exists()
    metrics = result.entities[0].metrics
    assert metrics["num_functions"] == 2
    assert metrics["num_classes"] == 1
    assert metrics["import_count"] == 1
    assert metrics["cyclomatic_complexity"] == 3
    assert metrics["max_function_complexity"] == 2


def test_typescript_and_tsx_without_resolution(
    source: Path, settings: Settings
) -> None:
    result = registry()["typescript"].analyze(
        source, ["script/sample.ts", "script/view.tsx"], settings, time.monotonic() + 20
    )
    assert not result.warnings
    assert len(result.entities) == 2
    assert result.entities[0].metrics["decision_count"] == 1
    assert result.entities[0].metrics["num_classes"] == 1
    assert "probability" not in result.model_dump_json()


@pytest.mark.parametrize(
    "language,filename",
    [
        ("java", "Broken.java"),
        ("python", "broken.py"),
        ("javascript", "broken.js"),
        ("typescript", "broken.ts"),
    ],
)
def test_syntax_errors(
    language: Language, filename: str, source: Path, settings: Settings
) -> None:
    (source / filename).write_text("class { (((")
    result = registry()[language].analyze(
        source, [filename], settings, time.monotonic() + 20
    )
    assert not result.entities
    assert result.warnings == [{"code": "FILE_PARSE_FAILED", "relative_path": filename}]


def test_discovery_deterministic_bounded_and_no_links(
    source: Path, tmp_path: Path, settings: Settings
) -> None:
    settings.max_archive_files = 100
    grouped, unsupported, warnings = discover(
        source, tmp_path / "copy", settings, time.monotonic() + 5
    )
    assert set(grouped) == {"java", "python", "javascript", "typescript"}
    assert unsupported == 0 and not warnings
    (source / "escape.py").symlink_to("/etc/passwd")
    with pytest.raises(AnalysisFailure, match="UNSAFE_SOURCE"):
        discover(source, tmp_path / "other", settings, time.monotonic() + 5)


def test_discovery_limits_skips_and_deadline(
    source: Path, tmp_path: Path, settings: Settings
) -> None:
    settings.max_archive_files = 100
    settings.max_analysis_file_bytes = 20
    grouped, _, warnings = discover(
        source, tmp_path / "small", settings, time.monotonic() + 5
    )
    assert not grouped
    assert all(warning["code"] == "FILE_TOO_LARGE" for warning in warnings)
    settings.max_archive_files = 1
    with pytest.raises(AnalysisFailure, match="SOURCE_LIMIT_EXCEEDED"):
        discover(source, tmp_path / "count", settings, time.monotonic() + 5)
    with pytest.raises(AnalysisFailure, match="ANALYZER_TIMEOUT"):
        discover(source, tmp_path / "timeout", settings, time.monotonic() - 1)


def test_trusted_process_timeout_and_failure(
    tmp_path: Path, settings: Settings
) -> None:
    # Commands here are fixed trusted test programs, never submitted content.
    with pytest.raises(AnalysisFailure, match="ANALYZER_TIMEOUT"):
        run_tool(
            [sys.executable, "-I", "-c", "import time; time.sleep(5)"],
            tmp_path,
            settings,
            time.monotonic() + 0.15,
        )
    with pytest.raises(AnalysisFailure, match="ANALYZER_FAILED"):
        run_tool(
            [sys.executable, "-I", "-c", "raise RuntimeError('private')"],
            tmp_path,
            settings,
            time.monotonic() + 5,
        )


def test_python_multiline_strings_encodings_and_schema(
    source: Path, settings: Settings
) -> None:
    (source / "edge.py").write_text(
        "class Worker:\n    @decorator\n"
        "    async def task(self, /, *args, flag=True, **kwargs):\n"
        '        text = """first\ncolumn zero\n        last"""\n'
        "        return text\n"
    )
    (source / "latin.py").write_bytes(
        b'# coding: latin-1\ndef label():\n    return "caf\xe9"\n'
    )
    (source / "bad.py").write_bytes(b"\xff\xfe")
    result = registry()["python"].analyze(
        source, ["edge.py", "latin.py", "bad.py"], settings, time.monotonic() + 20
    )
    assert len(result.entities) == 2
    entity = result.entities[0]
    assert entity.qualified_name == "Worker.task"
    assert entity.metrics["parameter_count"] == 4
    assert entity.metrics["loc"] == 5
    assert result.warnings == [{"code": "FILE_PARSE_FAILED", "relative_path": "bad.py"}]
    from app.analyzers.contracts import Entity

    for changes in (
        {"metric_schema_version": "javascript_file_v1"},
        {"entity_type": "file"},
        {"metrics": {"fake_probability": 0.5}},
        {"relative_path": "../escape.py"},
    ):
        with pytest.raises(ValidationError):
            Entity.model_validate({**entity.model_dump(), **changes})


def test_process_output_and_environment_boundary(
    tmp_path: Path, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("KAGEX_TEST_SECRET", "must-not-reach-parser")
    output = run_tool(
        [
            sys.executable,
            "-I",
            "-c",
            "import os; print(os.getenv('KAGEX_TEST_SECRET'))",
        ],
        tmp_path,
        settings,
        time.monotonic() + 5,
    )
    assert output.strip() == b"None"
    settings.max_analyzer_output_bytes = 1024
    with pytest.raises(AnalysisFailure):
        run_tool(
            [sys.executable, "-I", "-c", "print('a' * 100000)"],
            tmp_path,
            settings,
            time.monotonic() + 5,
        )


@pytest.mark.parametrize("language", ["java", "python", "javascript", "typescript"])
def test_submitted_side_effects_never_execute(
    language: Language, source: Path, tmp_path: Path, settings: Settings
) -> None:
    marker = tmp_path / "EXECUTED"
    quoted = json.dumps(str(marker))
    snippets = {
        "java": (
            "Sentinel.java",
            "public class Sentinel { static { try { new java.io.File("
            + quoted
            + ").createNewFile(); } catch (Exception e) {} } }",
        ),
        "python": (
            "sentinel.py",
            "from pathlib import Path\nPath("
            + quoted
            + ").touch()\ndef run(): return 1\n",
        ),
        "javascript": (
            "sentinel.js",
            "import fs from 'node:fs'; fs.writeFileSync(" + quoted + ", 'executed');",
        ),
        "typescript": (
            "sentinel.ts",
            "import fs from 'node:fs'; fs.writeFileSync(" + quoted + ", 'executed');",
        ),
    }
    filename, code = snippets[language]
    if language == "python":
        filename = "$(touch SHELL_EXECUTED).py"
    (source / filename).write_text(code)
    result = registry()[language].analyze(
        source, [filename], settings, time.monotonic() + 20
    )
    assert result.entities and not result.warnings
    assert not marker.exists()
    assert not (source.parent / "SHELL_EXECUTED").exists()


def test_script_extension_and_inline_config_policy(
    source: Path, settings: Settings
) -> None:
    files = {
        "view.jsx": "export const View = () => <div />;",
        "index.mjs": "/* eslint complexity: off */\n"
        "export function run(x) { if (x) return 1; return 0; }",
        "index.cjs": "const x = require('uninstalled'); module.exports = x;",
        "index.mts": "export const value: number = 1;",
        "index.cts": "import x = require('uninstalled'); export = x;",
    }
    for filename, code in files.items():
        (source / filename).write_text(code)
    js = registry()["javascript"].analyze(
        source, list(files)[:3], settings, time.monotonic() + 20
    )
    assert len(js.entities) == 3 and not js.warnings
    assert js.entities[1].metrics["cyclomatic_complexity"] == 2
    assert js.entities[2].metrics["coupling"] == 1
    ts = registry()["typescript"].analyze(
        source, list(files)[3:], settings, time.monotonic() + 20
    )
    assert len(ts.entities) == 2 and not ts.warnings
