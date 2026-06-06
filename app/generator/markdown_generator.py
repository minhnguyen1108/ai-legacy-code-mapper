from __future__ import annotations

import json
from pathlib import Path

from app.generator.mermaid_generator import erd, flowchart, sequence_diagram
from app.models import AnalysisReport, SourceRef


def source_label(source: SourceRef | None) -> str:
    if not source:
        return "chưa xác định"
    return f"`{source.file}:{source.line}` ({source.confidence})"


def generate_docs(report: AnalysisReport, output_dir: Path, risk_summary: str = "") -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "summary.md": summary_doc(report),
        "api-map.md": api_map_doc(report),
        "business-flows.md": business_flows_doc(report),
        "database-map.md": database_map_doc(report),
        "sequence-diagrams.md": sequence_doc(report),
        "risk-report.md": risk_doc(report, risk_summary),
        "analysis.json": json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
    }
    for filename, content in files.items():
        (output_dir / filename).write_text(content.rstrip() + "\n", encoding="utf-8")


def summary_doc(report: AnalysisReport) -> str:
    high = sum(risk.severity == "high" for risk in report.risks)
    medium = sum(risk.severity == "medium" for risk in report.risks)
    return f"""# Legacy Code Summary

## Project

- **Name:** {report.project_name}
- **Framework:** {report.framework} {report.framework_version}
- **Files scanned:** {report.files_scanned}
- **Routes:** {len(report.routes)}
- **Business flows:** {len(report.flows)}
- **Models:** {len(report.models)}
- **Tables:** {len(report.tables)}
- **Risks:** {len(report.risks)} ({high} high, {medium} medium)
- **Generated:** {report.generated_at}

## Architecture Overview

```mermaid
flowchart LR
    Source["Laravel Source"] --> Scanner["Static Scanner"]
    Scanner --> Routes["Routes"]
    Scanner --> Classes["Controllers / Services / Repositories"]
    Scanner --> Database["Models / Migrations"]
    Routes --> Graph["Relationship Graph"]
    Classes --> Graph
    Database --> Graph
    Graph --> Docs["Generated Documentation"]
```

## Notes

- Source code was analyzed statically and was not executed.
- `confirmed` means a direct source mapping was found.
- `inferred` means the relationship follows Laravel conventions but lacks a concrete method declaration.
- Dynamic container bindings, runtime routes, macros and raw SQL may require manual review.
"""


def api_map_doc(report: AnalysisReport) -> str:
    lines = [
        "# API Mapping",
        "",
        "| Method | Path | Controller | Middleware | Source |",
        "|---|---|---|---|---|",
    ]
    for route in report.routes:
        controller = (
            f"`{route.controller}@{route.action}`"
            if route.controller and route.action
            else "chưa xác định"
        )
        middleware = ", ".join(route.middleware) or "-"
        lines.append(
            f"| {route.method} | `{route.path}` | {controller} | {middleware} | {source_label(route.source)} |"
        )
    if not report.routes:
        lines.append("| - | - | Không tìm thấy route tĩnh | - | - |")
    return "\n".join(lines)


def business_flows_doc(report: AnalysisReport) -> str:
    lines = ["# Business Flows", ""]
    for flow in report.flows:
        lines.extend(
            [
                f"## Flow: {flow.title}",
                "",
                f"**Route:** `{flow.route.method} {flow.route.path}`",
                "",
                f"**Controller:** `{flow.route.controller}@{flow.route.action}`",
                "",
                "**Call chain:**",
                "",
            ]
        )
        if flow.steps:
            lines.extend(
                f"{index}. `{step.class_name}::{step.method_name}` — {source_label(step.source)}"
                for index, step in enumerate(flow.steps, 1)
            )
        else:
            lines.append("- Chưa xác định")
        lines.extend(
            [
                "",
                "**Tables:** " + (", ".join(f"`{table}`" for table in flow.tables) or "chưa xác định"),
                "",
                "**Business meaning:**",
                "",
                flow.business_meaning,
                "",
                "```mermaid",
                flowchart(flow),
                "```",
                "",
            ]
        )
    if not report.flows:
        lines.append("Không tìm thấy business flow tĩnh.")
    return "\n".join(lines)


def database_map_doc(report: AnalysisReport) -> str:
    lines = ["# Database Map", "", "## ERD", "", "```mermaid", erd(report), "```", ""]
    for table in report.tables:
        lines.extend([f"## Table: {table.name}", "", f"Source: {source_label(table.source)}", "", "### Columns", ""])
        lines.extend(
            f"- `{column.name}`: {column.type}{' (nullable)' if column.nullable else ''}"
            for column in table.columns
        )
        lines.extend(["", "### Foreign Keys", ""])
        if table.foreign_keys:
            lines.extend(
                f"- `{foreign.column}` → `{foreign.target_table}.{foreign.target_column}`"
                for foreign in table.foreign_keys
            )
        else:
            lines.append("- Không tìm thấy foreign key tĩnh.")
        lines.extend(["", "### Used By", ""])
        lines.extend(f"- {user}" for user in table.used_by)
        if not table.used_by:
            lines.append("- Chưa xác định")
        lines.append("")
    return "\n".join(lines)


def sequence_doc(report: AnalysisReport) -> str:
    lines = ["# Sequence Diagrams", ""]
    for flow in report.flows:
        lines.extend(
            [
                f"## {flow.title}",
                "",
                "```mermaid",
                sequence_diagram(flow),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def risk_doc(report: AnalysisReport, ai_summary: str) -> str:
    lines = ["# Risk Report", ""]
    if ai_summary:
        lines.extend(["## AI Summary", "", ai_summary, ""])
    lines.extend(
        [
            "Static findings are review signals, not confirmed vulnerabilities.",
            "",
            "| Severity | Category | Finding | Source | Recommendation |",
            "|---|---|---|---|---|",
        ]
    )
    for risk in sorted(
        report.risks,
        key=lambda item: {"high": 0, "medium": 1, "low": 2}.get(item.severity, 3),
    ):
        lines.append(
            f"| {risk.severity.upper()} | {risk.category} | {risk.message} | "
            f"{source_label(risk.source)} | {risk.recommendation} |"
        )
    if not report.risks:
        lines.append("| - | - | Không tìm thấy rule-based risk trong phạm vi MVP. | - | - |")
    return "\n".join(lines)
