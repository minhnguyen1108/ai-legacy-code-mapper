from __future__ import annotations

import re

from app.models import ModelInfo, Relationship, SourceRef
from app.scanner.php_parser import ClassInfo


def snake_case(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()


def pluralize(value: str) -> str:
    if value.endswith("y") and not value.endswith(("ay", "ey", "iy", "oy", "uy")):
        return f"{value[:-1]}ies"
    if value.endswith(("s", "x", "z", "ch", "sh")):
        return f"{value}es"
    return f"{value}s"


def scan_models(classes: list[ClassInfo]) -> list[ModelInfo]:
    models: list[ModelInfo] = []
    for class_info in classes:
        is_model = class_info.parent == "Model" or "/Models/" in f"/{class_info.file.relative_path}"
        if not is_model:
            continue
        table_match = re.search(
            r"(?:protected|public)\s+\$table\s*=\s*['\"]([^'\"]+)['\"]",
            class_info.file.content,
        )
        fillable_match = re.search(
            r"(?:protected|public)\s+\$fillable\s*=\s*\[(.*?)\]",
            class_info.file.content,
            re.DOTALL,
        )
        fillable = (
            re.findall(r"['\"]([^'\"]+)['\"]", fillable_match.group(1))
            if fillable_match
            else []
        )
        relationships: list[Relationship] = []
        for method in class_info.methods.values():
            relation_match = re.search(
                r"\$this->(belongsTo|hasOne|hasMany|belongsToMany|morphOne|morphMany)"
                r"\s*\(\s*([\\\w]+)::class",
                method.body,
            )
            if relation_match:
                relationships.append(
                    Relationship(
                        kind=relation_match.group(1),
                        target=relation_match.group(2).rsplit("\\", 1)[-1],
                        name=method.name,
                        source=SourceRef(class_info.file.relative_path, method.line),
                    )
                )
        models.append(
            ModelInfo(
                name=class_info.name,
                table=table_match.group(1)
                if table_match
                else pluralize(snake_case(class_info.name)),
                fillable=fillable,
                relationships=relationships,
                source=SourceRef(class_info.file.relative_path, class_info.line),
            )
        )
    return models
