import base64
from pathlib import Path

from app.analyzers.contracts import AnalysisFailure, Entity, Result
from app.analyzers.process import run_tool
from app.core.config import Settings


class JavaAnalyzer:
    def analyze(
        self, root: Path, paths: list[str], settings: Settings, deadline: float
    ) -> Result:
        manifest = root.parent / "java-files.txt"
        manifest.write_text("\n".join(paths))
        tools = settings.analyzer_tools_root
        output = run_tool(
            [
                str(settings.analyzer_java),
                "-Xmx512m",
                "-Dfile.encoding=UTF-8",
                "-cp",
                f"{tools / 'ck.jar'}:{tools}",
                "KagexCK",
                str(root),
                str(manifest),
            ],
            root.parent,
            settings,
            deadline,
        )
        result = Result()
        for line in output.decode().splitlines():
            columns = line.split("\t")
            if columns[0] == "W":
                result.warnings.append(
                    {
                        "code": columns[1],
                        "relative_path": base64.b64decode(columns[2]).decode(),
                    }
                )
                continue
            if columns[0] != "E" or len(columns) != 14:
                raise AnalysisFailure(
                    "ANALYZER_FAILED", "Java analyzer returned invalid output."
                )
            relative, name = (
                base64.b64decode(value).decode() for value in columns[1:3]
            )
            if relative not in paths:
                raise AnalysisFailure(
                    "ANALYZER_FAILED", "Java analyzer returned an unknown source."
                )
            result.entities.append(
                Entity(
                    language="java",
                    entity_type="class",
                    relative_path=relative,
                    qualified_name=name,
                    start_line=int(columns[3]),
                    end_line=int(columns[4]),
                    metrics=dict(
                        zip(
                            [
                                "wmc",
                                "dit",
                                "noc",
                                "cbo",
                                "rfc",
                                "lcom",
                                "loc",
                                "num_functions",
                            ],
                            map(int, columns[5:13]),
                            strict=True,
                        )
                    ),
                    analyzer_name="ck",
                    analyzer_version=f"0.7.0/jdt-java11/java-{columns[13]}",
                    metric_schema_version="java_class_v1",
                    warnings=["UNRESOLVED_DEPENDENCIES_POSSIBLE"],
                )
            )
        return result
