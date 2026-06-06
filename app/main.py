from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.pipeline import analyze
from app.source import resolve_source


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-legacy-code-mapper",
        description="Reverse engineer legacy Laravel code into Markdown and Mermaid documentation.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a local path or Git repository.")
    analyze_parser.add_argument("source", help="Project path or Git URL.")
    analyze_parser.add_argument("--framework", default="laravel", choices=["laravel"])
    analyze_parser.add_argument("--provider", default="none", choices=["none", "openai", "ollama"])
    analyze_parser.add_argument("--model", help="AI model override.")
    analyze_parser.add_argument("--language", default="vi", choices=["vi", "en"])
    analyze_parser.add_argument("--output", help="Output directory. Defaults to <project>/docs/generated.")
    analyze_parser.add_argument("--json", action="store_true", help="Print the JSON report.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = None
    try:
        print("[...] Resolve source")
        source = resolve_source(args.source)
        if args.output:
            output_dir = Path(args.output).resolve()
        elif source.temporary:
            output_dir = Path.cwd() / "docs" / "generated"
        else:
            output_dir = source.path / "docs" / "generated"
        report = analyze(
            project_path=source.path,
            output_dir=output_dir,
            provider_name=args.provider,
            model=args.model,
            language=args.language,
        )
        if args.json:
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        print(f"\n[OK] Docs generated at: {output_dir}")
        return 0
    except (ValueError, RuntimeError, OSError) as error:
        print(f"\n[ERROR] Analysis failed: {error}", file=sys.stderr)
        return 1
    finally:
        if source:
            source.cleanup()
