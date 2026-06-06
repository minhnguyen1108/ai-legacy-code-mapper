from __future__ import annotations

import re

from app.models import AnalysisReport, BusinessFlow


def safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", value)


def sequence_diagram(flow: BusinessFlow) -> str:
    lines = ["sequenceDiagram", "    actor User"]
    previous = "User"
    aliases: list[str] = []
    for index, step in enumerate(flow.steps):
        alias = f"S{index}"
        aliases.append(alias)
        lines.append(f"    participant {alias} as {step.class_name}")
        lines.append(f"    {previous}->>+{alias}: {step.method_name}()")
        previous = alias
    for index, table in enumerate(flow.tables):
        alias = f"DB{index}"
        lines.append(f"    participant {alias} as {table}")
        lines.append(f"    {previous}->>{alias}: read / write")
    for index in range(len(aliases) - 1, -1, -1):
        target = aliases[index - 1] if index else "User"
        lines.append(f"    {aliases[index]}-->>-{target}: result")
    return "\n".join(lines)


def flowchart(flow: BusinessFlow) -> str:
    route_label = f"{flow.route.method} {flow.route.path}"
    lines = ["flowchart TD", f'    U["User"] --> R["{route_label}"]']
    previous = "R"
    for index, step in enumerate(flow.steps):
        current = f"S{index}"
        lines.append(
            f'    {previous} --> {current}["{step.class_name}::{step.method_name}"]'
        )
        previous = current
    for index, table in enumerate(flow.tables):
        current = f"DB{index}"
        lines.append(f'    {previous} --> {current}[("{table}")]')
        previous = current
    return "\n".join(lines)


def erd(report: AnalysisReport) -> str:
    lines = ["erDiagram"]
    for table in report.tables:
        table_id = safe_id(table.name)
        lines.append(f"    {table_id} {{")
        for column in table.columns:
            lines.append(f"        {safe_id(column.type)} {safe_id(column.name)}")
        lines.append("    }")
        for foreign in table.foreign_keys:
            lines.append(
                f'    {safe_id(foreign.target_table)} ||--o{{ {table_id} : "{foreign.column}"'
            )
    return "\n".join(lines)
