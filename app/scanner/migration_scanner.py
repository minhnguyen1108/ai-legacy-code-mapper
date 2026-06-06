from __future__ import annotations

import re

from app.models import Column, ForeignKey, SourceRef, TableInfo
from app.scanner.file_scanner import PhpFile
from app.scanner.php_parser import line_number


COLUMN_TYPES = (
    "id|increments|bigIncrements|integer|bigInteger|unsignedInteger|"
    "unsignedBigInteger|string|char|text|mediumText|longText|boolean|"
    "date|dateTime|timestamp|decimal|float|double|json|jsonb|uuid|enum"
)


def scan_migrations(files: list[PhpFile]) -> list[TableInfo]:
    by_name: dict[str, TableInfo] = {}
    migration_files = [
        file for file in files if file.relative_path.startswith("database/migrations/")
    ]
    schema_pattern = re.compile(
        r"Schema::(create|table)\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*"
        r"function\s*\([^)]*\$table[^)]*\)\s*\{(.*?)\}\s*\)",
        re.DOTALL,
    )
    for file in migration_files:
        for match in schema_pattern.finditer(file.content):
            table_name = match.group(2)
            body = match.group(3)
            table = by_name.setdefault(
                table_name,
                TableInfo(
                    name=table_name,
                    columns=[],
                    foreign_keys=[],
                    source=SourceRef(file.relative_path, line_number(file.content, match.start())),
                ),
            )
            column_pattern = re.compile(
                rf"\$table->({COLUMN_TYPES})\s*\(\s*(?:['\"]([^'\"]+)['\"])?(.*?)\)\s*;",
                re.DOTALL,
            )
            for column_match in column_pattern.finditer(body):
                column_type, name, modifiers = column_match.groups()
                if column_type == "id":
                    name = name or "id"
                elif column_type in {"increments", "bigIncrements"}:
                    name = name or "id"
                if not name:
                    continue
                if not any(column.name == name for column in table.columns):
                    table.columns.append(
                        Column(
                            name=name,
                            type=column_type,
                            nullable="->nullable(" in modifiers,
                        )
                    )
            if re.search(r"\$table->timestamps\s*\(", body):
                for timestamp_name in ("created_at", "updated_at"):
                    if not any(column.name == timestamp_name for column in table.columns):
                        table.columns.append(Column(timestamp_name, "timestamp", True))

            for foreign in re.finditer(
                r"\$table->foreign\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
                r"\s*->references\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
                r"\s*->on\s*\(\s*['\"]([^'\"]+)['\"]",
                body,
            ):
                key = ForeignKey(
                    column=foreign.group(1),
                    target_column=foreign.group(2),
                    target_table=foreign.group(3),
                )
                if key not in table.foreign_keys:
                    table.foreign_keys.append(key)
            for constrained in re.finditer(
                r"\$table->foreignId\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
                r"(?:\s*->constrained\s*\(\s*['\"]?([^'\")]+)?['\"]?\s*\))?",
                body,
            ):
                column = constrained.group(1)
                target = constrained.group(2) or f"{column.removesuffix('_id')}s"
                table.foreign_keys.append(ForeignKey(column, target))
    return list(by_name.values())
