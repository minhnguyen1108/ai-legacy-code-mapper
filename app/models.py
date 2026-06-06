from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SourceRef:
    file: str
    line: int
    confidence: str = "confirmed"


@dataclass
class Route:
    method: str
    path: str
    controller: str | None
    action: str | None
    name: str | None
    middleware: list[str]
    source: SourceRef


@dataclass
class CallStep:
    kind: str
    class_name: str
    method_name: str
    source: SourceRef
    snippet: str = ""


@dataclass
class Relationship:
    kind: str
    target: str
    name: str
    source: SourceRef


@dataclass
class ModelInfo:
    name: str
    table: str
    fillable: list[str]
    relationships: list[Relationship]
    source: SourceRef


@dataclass
class Column:
    name: str
    type: str
    nullable: bool = False


@dataclass
class ForeignKey:
    column: str
    target_table: str
    target_column: str = "id"


@dataclass
class TableInfo:
    name: str
    columns: list[Column]
    foreign_keys: list[ForeignKey]
    source: SourceRef
    used_by: list[str] = field(default_factory=list)


@dataclass
class Risk:
    severity: str
    category: str
    message: str
    source: SourceRef | None = None
    recommendation: str = ""


@dataclass
class BusinessFlow:
    title: str
    route: Route
    steps: list[CallStep]
    tables: list[str]
    business_meaning: str
    risks: list[Risk] = field(default_factory=list)


@dataclass
class AnalysisReport:
    project_name: str
    project_path: str
    framework: str
    framework_version: str
    generated_at: str
    routes: list[Route]
    flows: list[BusinessFlow]
    models: list[ModelInfo]
    tables: list[TableInfo]
    risks: list[Risk]
    files_scanned: int
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
