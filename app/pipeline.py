from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.ai.factory import create_provider
from app.ai.prompts import SYSTEM_PROMPT_VI, business_flow_prompt, risk_summary_prompt
from app.generator.markdown_generator import generate_docs
from app.graph.call_graph import build_call_chain
from app.graph.db_graph import attach_table_usage, tables_for_flow
from app.models import AnalysisReport, BusinessFlow
from app.risk_analyzer import analyze_risks
from app.scanner.file_scanner import scan_php_files
from app.scanner.migration_scanner import scan_migrations
from app.scanner.model_scanner import scan_models
from app.scanner.php_parser import parse_class
from app.scanner.route_scanner import scan_routes


def detect_laravel_version(project_path: Path) -> str:
    composer_path = project_path / "composer.json"
    if not composer_path.is_file():
        return "chưa xác định"
    try:
        composer = json.loads(composer_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "chưa xác định"
    return composer.get("require", {}).get("laravel/framework", "chưa xác định")


def fallback_meaning(flow: BusinessFlow) -> str:
    chain = " → ".join(step.class_name for step in flow.steps) or "chưa xác định"
    tables = ", ".join(flow.tables) or "chưa xác định"
    return (
        f"Request `{flow.route.method} {flow.route.path}` được xử lý qua {chain}. "
        f"Dữ liệu liên quan tới bảng {tables}. Ý nghĩa nghiệp vụ chi tiết chưa xác định "
        "nếu không có tên miền nghiệp vụ hoặc AI explainer."
    )


def title_for_flow(route_path: str, action: str | None) -> str:
    label = action or route_path.strip("/").replace("/", " ")
    spaced = "".join(f" {char}" if char.isupper() else char for char in label).strip()
    return spaced.replace("_", " ").replace("-", " ").title()


def analyze(
    project_path: Path,
    output_dir: Path,
    provider_name: str = "none",
    model: str | None = None,
    language: str = "vi",
) -> AnalysisReport:
    print("[OK] Scan PHP files")
    files = scan_php_files(project_path)
    if not files:
        raise ValueError("No PHP files were found in the project.")

    print("[OK] Scan routes and classes")
    classes = [parsed for file in files if (parsed := parse_class(file))]
    class_map = {class_info.name: class_info for class_info in classes}
    routes = scan_routes(files)

    print("[OK] Build call graph")
    models = scan_models(classes)
    tables = scan_migrations(files)
    attach_table_usage(tables, models, class_map)
    risks = analyze_risks(files, classes)
    flows: list[BusinessFlow] = []
    for route in routes:
        steps = build_call_chain(route, class_map)
        flow = BusinessFlow(
            title=title_for_flow(route.path, route.action),
            route=route,
            steps=steps,
            tables=tables_for_flow(steps, class_map, models),
            business_meaning="",
        )
        flow.business_meaning = fallback_meaning(flow)
        flows.append(flow)

    report = AnalysisReport(
        project_name=project_path.name,
        project_path=str(project_path),
        framework="Laravel",
        framework_version=detect_laravel_version(project_path),
        generated_at=datetime.now(timezone.utc).isoformat(),
        routes=routes,
        flows=flows,
        models=models,
        tables=tables,
        risks=risks,
        files_scanned=len(files),
        warnings=[],
    )
    if not routes:
        report.warnings.append("Không tìm thấy route tĩnh được hỗ trợ.")
    if not tables:
        report.warnings.append("Không tìm thấy migration Schema được hỗ trợ.")

    risk_summary = ""
    if provider_name != "none":
        print(f"[...] Explain business flows with {provider_name}")
        provider = create_provider(provider_name, model, Path.cwd())
        for flow in report.flows:
            try:
                explanation = provider.complete(SYSTEM_PROMPT_VI, business_flow_prompt(flow))
                if explanation:
                    flow.business_meaning = explanation
            except RuntimeError as error:
                report.warnings.append(f"AI flow explanation failed: {error}")
                break
        if risks:
            try:
                risk_summary = provider.complete(SYSTEM_PROMPT_VI, risk_summary_prompt(risks))
            except RuntimeError as error:
                report.warnings.append(f"AI risk summary failed: {error}")

    print("[OK] Generate Markdown and Mermaid docs")
    generate_docs(report, output_dir, risk_summary)
    return report
