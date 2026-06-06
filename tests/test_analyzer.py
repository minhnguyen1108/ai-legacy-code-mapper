from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.pipeline import analyze
from app.source import is_git_url, resolve_source


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "laravel5-support"


class AnalyzerTest(unittest.TestCase):
    def test_detects_supported_git_urls(self) -> None:
        self.assertTrue(is_git_url("https://github.com/company/project.git"))
        self.assertTrue(is_git_url("git@github.com:company/project.git"))
        self.assertFalse(is_git_url("./legacy-project"))

    def test_accepts_accidental_dot_before_windows_absolute_path(self) -> None:
        resolved = resolve_source(f".{EXAMPLE}")
        self.assertEqual(resolved.path, EXAMPLE.resolve())

    def test_laravel5_project_generates_expected_graph_and_docs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "generated"
            report = analyze(EXAMPLE, output, provider_name="none")

            self.assertEqual(report.framework_version, "5.8.*")
            self.assertEqual(len(report.routes), 2)
            self.assertEqual(report.routes[0].path, "/api/report/create")
            self.assertEqual(report.routes[0].middleware, ["auth:api"])
            self.assertEqual(
                [step.class_name for step in report.flows[0].steps],
                [
                    "ReportController",
                    "ReportService",
                    "ReportRepository",
                    "CustomerReport",
                    "ReportRepository",
                    "ReportHistory",
                ],
            )
            self.assertEqual(
                report.flows[0].tables,
                ["customer_reports", "report_histories"],
            )
            self.assertEqual({table.name for table in report.tables}, {
                "customer_reports",
                "report_histories",
            })
            self.assertTrue(any(risk.category == "database" for risk in report.risks))
            for filename in (
                "api-map.md",
                "business-flows.md",
                "database-map.md",
                "sequence-diagrams.md",
                "risk-report.md",
                "summary.md",
                "analysis.json",
            ):
                self.assertTrue((output / filename).is_file(), filename)

            business_flows = (output / "business-flows.md").read_text(encoding="utf-8")
            self.assertIn("ReportController::create", business_flows)
            self.assertIn("report_histories", business_flows)


if __name__ == "__main__":
    unittest.main()
