from __future__ import annotations

import re

from app.models import CallStep, Route, SourceRef
from app.scanner.php_parser import ClassInfo, MethodInfo


IGNORED_STATIC_CLASSES = {
    "App",
    "Auth",
    "Cache",
    "Config",
    "DB",
    "Log",
    "Mail",
    "Redirect",
    "Request",
    "Response",
    "Route",
    "Schema",
    "Validator",
}


def classify_class(name: str) -> str:
    for suffix, kind in (
        ("Controller", "controller"),
        ("Service", "service"),
        ("Repository", "repository"),
        ("Job", "job"),
        ("Event", "event"),
        ("Listener", "listener"),
    ):
        if name.endswith(suffix):
            return kind
    return "model"


def compact_snippet(method: MethodInfo) -> str:
    body = " ".join(line.strip() for line in method.body.splitlines() if line.strip())
    return body[:500]


def build_call_chain(
    route: Route, class_map: dict[str, ClassInfo], max_depth: int = 10
) -> list[CallStep]:
    steps: list[CallStep] = []
    visited: set[tuple[str, str]] = set()

    def visit(class_name: str | None, method_name: str | None, depth: int) -> None:
        if not class_name or not method_name or depth > max_depth:
            return
        key = (class_name, method_name)
        if key in visited:
            return
        visited.add(key)
        class_info = class_map.get(class_name)
        if not class_info:
            return
        method = class_info.methods.get(method_name)
        steps.append(
            CallStep(
                kind=classify_class(class_name),
                class_name=class_name,
                method_name=method_name,
                source=SourceRef(
                    class_info.file.relative_path,
                    method.line if method else class_info.line,
                    "confirmed" if method else "inferred",
                ),
                snippet=compact_snippet(method) if method else "",
            )
        )
        if not method:
            return

        calls: list[tuple[int, str, str]] = []
        for match in re.finditer(r"\$this->(\w+)->(\w+)\s*\(", method.body):
            target = class_info.property_types.get(match.group(1))
            if target:
                calls.append((match.start(), target, match.group(2)))
        for match in re.finditer(r"\b([A-Z]\w*)::(\w+)\s*\(", method.body):
            target, called_method = match.group(1), match.group(2)
            if target not in IGNORED_STATIC_CLASSES and target in class_map:
                calls.append((match.start(), target, called_method))
        for _, target, called_method in sorted(calls):
            visit(target, called_method, depth + 1)

    visit(route.controller, route.action, 0)
    return steps
