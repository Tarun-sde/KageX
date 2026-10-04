"""Trusted isolated Python parser entry point; never import submitted modules."""

import ast
import io
import json
import resource
import sys
import tokenize
from pathlib import Path
from typing import Any

import radon
from radon.complexity import cc_visit_ast
from radon.metrics import h_visit_ast, mi_visit
from radon.raw import analyze


def analyze_python(root: Path, paths: list[str]) -> dict[str, Any]:
    entities: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    for relative in paths:
        try:
            raw = (root / relative).read_bytes()
            encoding, _ = tokenize.detect_encoding(io.BytesIO(raw).readline)
            source = raw.decode(encoding)
            tree = ast.parse(source)
        except SyntaxError, UnicodeError, LookupError, ValueError, RecursionError:
            warnings.append({"code": "FILE_PARSE_FAILED", "relative_path": relative})
            continue
        lines = source.splitlines()

        def visit(
            node: ast.AST,
            scope: list[str],
            lines: list[str] = lines,
            relative: str = relative,
            entities: list[dict[str, Any]] = entities,
        ) -> None:
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    qualified = ".".join([*scope, child.name])
                    end = child.end_lineno or child.lineno
                    snippet = "\n".join(lines[child.lineno - 1 : end])
                    raw_metrics = analyze(snippet)
                    halstead = h_visit_ast(child).total
                    descendants = list(ast.walk(child))
                    metrics = {
                        "loc": end - child.lineno + 1,
                        "sloc": raw_metrics.sloc,
                        "cyclomatic_complexity": cc_visit_ast(child)[0].complexity,
                        "halstead_volume": halstead.volume,
                        "halstead_difficulty": halstead.difficulty,
                        "halstead_effort": halstead.effort,
                        # Normalize indentation without corrupting multiline strings.
                        # This MI measures the AST-rendered function, without comments.
                        "maintainability_index": mi_visit(
                            ast.unparse(child), multi=True
                        ),
                        "comment_density": (raw_metrics.comments + raw_metrics.multi)
                        / max(raw_metrics.loc, 1),
                        "parameter_count": len(child.args.posonlyargs)
                        + len(child.args.args)
                        + len(child.args.kwonlyargs)
                        + int(child.args.vararg is not None)
                        + int(child.args.kwarg is not None),
                        "branch_count": sum(
                            isinstance(item, (ast.If, ast.IfExp, ast.Match))
                            for item in descendants
                        ),
                        "loop_count": sum(
                            isinstance(item, (ast.For, ast.AsyncFor, ast.While))
                            for item in descendants
                        ),
                        "return_count": sum(
                            isinstance(item, ast.Return) for item in descendants
                        ),
                        "num_functions": sum(
                            isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                            for item in descendants
                        )
                        - 1,
                        "num_classes": sum(
                            isinstance(item, ast.ClassDef) for item in descendants
                        ),
                        "import_count": sum(
                            isinstance(item, (ast.Import, ast.ImportFrom))
                            for item in descendants
                        ),
                    }
                    entities.append(
                        dict(
                            language="python",
                            entity_type="function",
                            relative_path=relative,
                            qualified_name=qualified,
                            start_line=child.lineno,
                            end_line=end,
                            metrics=metrics,
                            analyzer_name="radon+ast",
                            analyzer_version=f"{radon.__version__}/python-{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                            metric_schema_version="python_function_v1",
                            warnings=[],
                        )
                    )
                    visit(child, [*scope, child.name, "<locals>"])
                elif isinstance(child, ast.ClassDef):
                    visit(child, [*scope, child.name])
                else:
                    visit(child, scope)

        try:
            visit(tree, [])
        except RecursionError, SyntaxError, ValueError:
            entities = [
                entity for entity in entities if entity["relative_path"] != relative
            ]
            warnings.append({"code": "FILE_PARSE_FAILED", "relative_path": relative})
    return {"entities": entities, "warnings": warnings}


if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1048576, 512 * 1048576))
    manifest = json.loads(Path(sys.argv[1]).read_text())
    print(
        json.dumps(
            analyze_python(Path(manifest["root"]), manifest["paths"]), allow_nan=False
        )
    )
