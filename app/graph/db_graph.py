from __future__ import annotations

import re

from app.models import CallStep, ModelInfo, TableInfo
from app.scanner.php_parser import ClassInfo


def tables_for_flow(
    steps: list[CallStep],
    classes: dict[str, ClassInfo],
    models: list[ModelInfo],
) -> list[str]:
    model_tables = {model.name: model.table for model in models}
    tables: list[str] = []
    for step in steps:
        if step.class_name in model_tables:
            tables.append(model_tables[step.class_name])
        class_info = classes.get(step.class_name)
        method = class_info.methods.get(step.method_name) if class_info else None
        if not method:
            continue
        for match in re.finditer(r"DB::table\s*\(\s*['\"]([^'\"]+)['\"]", method.body):
            tables.append(match.group(1))
        for model_name, table_name in model_tables.items():
            if re.search(rf"\b{re.escape(model_name)}::\w+\s*\(", method.body):
                tables.append(table_name)
            if re.search(rf"\bnew\s+{re.escape(model_name)}\b", method.body):
                tables.append(table_name)
    return list(dict.fromkeys(tables))


def attach_table_usage(
    tables: list[TableInfo],
    models: list[ModelInfo],
    classes: dict[str, ClassInfo],
) -> None:
    for table in tables:
        users: list[str] = []
        for model in models:
            if model.table == table.name:
                users.append(f"{model.name} model")
        table_pattern = re.compile(rf"['\"]{re.escape(table.name)}['\"]")
        for class_info in classes.values():
            if (
                not class_info.file.relative_path.startswith("database/migrations/")
                and not any(model.name == class_info.name and model.table == table.name for model in models)
                and table_pattern.search(class_info.file.content)
            ):
                users.append(class_info.name)
        table.used_by = list(dict.fromkeys(users))
