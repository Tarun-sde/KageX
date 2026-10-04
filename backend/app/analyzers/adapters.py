import json
import sys
from pathlib import Path

from app.analyzers.contracts import Analyzer, Language, Result
from app.analyzers.process import run_tool
from app.core.config import Settings


class PythonAnalyzer:
    def analyze(
        self, root: Path, paths: list[str], settings: Settings, deadline: float
    ) -> Result:
        manifest = root.parent / "python.json"
        manifest.write_text(json.dumps({"root": str(root), "paths": paths}))
        return Result.model_validate_json(
            run_tool(
                [
                    sys.executable,
                    "-I",
                    str(Path(__file__).with_name("python_tool.py")),
                    str(manifest),
                ],
                root.parent,
                settings,
                deadline,
            )
        )


class ScriptAnalyzer:
    def __init__(self, language: Language) -> None:
        self.language = language

    def analyze(
        self, root: Path, paths: list[str], settings: Settings, deadline: float
    ) -> Result:
        manifest = root.parent / f"{self.language}.json"
        manifest.write_text(
            json.dumps({"root": str(root), "paths": paths, "language": self.language})
        )
        return Result.model_validate_json(
            run_tool(
                [
                    str(settings.analyzer_node),
                    "--max-old-space-size=256",
                    str(settings.analyzer_tools_root / "script.mjs"),
                    str(manifest),
                ],
                root.parent,
                settings,
                deadline,
            )
        )


def registry() -> dict[Language, Analyzer]:
    from app.analyzers.java import JavaAnalyzer

    return {
        "python": PythonAnalyzer(),
        "java": JavaAnalyzer(),
        "javascript": ScriptAnalyzer("javascript"),
        "typescript": ScriptAnalyzer("typescript"),
    }
