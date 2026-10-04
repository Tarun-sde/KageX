from pathlib import Path, PurePosixPath
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.config import Settings

Language = Literal["java", "python", "javascript", "typescript"]
EXTENSIONS: dict[str, Language] = {
    ".java": "java",
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
}

# Feature sets are schema contracts, not model feature ordering.
SCHEMAS: dict[Language, tuple[str, str, set[str]]] = {
    "java": (
        "class",
        "java_class_v1",
        set("wmc dit noc cbo rfc lcom loc num_functions".split()),
    ),
    "python": (
        "function",
        "python_function_v1",
        set(
            "loc sloc cyclomatic_complexity halstead_volume halstead_difficulty "
            "halstead_effort maintainability_index comment_density parameter_count "
            "branch_count loop_count "
            "return_count num_functions num_classes import_count".split()
        ),
    ),
    "javascript": (
        "file",
        "javascript_file_v1",
        set(
            "loc num_functions num_classes import_count coupling cyclomatic_complexity "
            "max_function_complexity complexity_units".split()
        ),
    ),
    "typescript": (
        "file",
        "typescript_file_v1",
        set(
            "loc num_functions num_classes import_count coupling decision_count".split()
        ),
    ),
}


class Entity(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    language: Language
    entity_type: Literal["class", "function", "file"]
    relative_path: str = Field(max_length=512)
    qualified_name: str = Field(max_length=1024)
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    metrics: dict[str, int | float | None]
    analyzer_name: str = Field(min_length=1, max_length=100)
    analyzer_version: str = Field(min_length=1, max_length=100)
    metric_schema_version: str = Field(max_length=60)
    warnings: list[str] = []

    @model_validator(mode="after")
    def validate_contract(self) -> Entity:
        kind, version, features = SCHEMAS[self.language]
        path = PurePosixPath(self.relative_path)
        if (
            path.is_absolute()
            or ".." in path.parts
            or "\\" in self.relative_path
            or not path.name
            or self.end_line < self.start_line
        ):
            raise ValueError("Invalid entity location")
        if (
            self.entity_type != kind
            or self.metric_schema_version != version
            or set(self.metrics) != features
        ):
            raise ValueError("Entity does not match its metric schema")
        return self


class Result(BaseModel):
    entities: list[Entity] = []
    warnings: list[dict[str, str]] = []


class Analyzer(Protocol):
    def analyze(
        self, root: Path, paths: list[str], settings: Settings, deadline: float
    ) -> Result: ...


class AnalysisFailure(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code, self.message = code, message
        super().__init__(code)
