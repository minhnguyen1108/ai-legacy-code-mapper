from __future__ import annotations

import re

from app.models import Route, SourceRef
from app.scanner.file_scanner import PhpFile
from app.scanner.php_parser import line_number


HTTP_METHODS = "get|post|put|patch|delete|options|any"


def _route_context(content: str, index: int) -> tuple[list[str], str]:
    prefix = content[:index]
    middleware: list[str] = []
    path_prefix = ""
    group_matches = list(
        re.finditer(
            r"Route::group\s*\(\s*\[(.*?)\]\s*,\s*function\s*\([^)]*\)\s*\{",
            prefix,
            re.DOTALL,
        )
    )
    if group_matches:
        config = group_matches[-1].group(1)
        prefix_match = re.search(r"['\"]prefix['\"]\s*=>\s*['\"]([^'\"]+)['\"]", config)
        middleware_match = re.search(
            r"['\"]middleware['\"]\s*=>\s*(?:\[\s*)?['\"]([^'\"]+)['\"]", config
        )
        path_prefix = prefix_match.group(1) if prefix_match else ""
        if middleware_match:
            middleware.extend(item.strip() for item in middleware_match.group(1).split(","))
    return middleware, path_prefix


def scan_routes(files: list[PhpFile]) -> list[Route]:
    routes: list[Route] = []
    route_files = [
        file
        for file in files
        if file.relative_path.startswith("routes/")
        or file.relative_path == "app/Http/routes.php"
    ]
    pattern = re.compile(
        rf"Route::({HTTP_METHODS})\s*\(\s*(['\"])(.*?)\2\s*,\s*"
        r"(?:(['\"])(.*?)\4|\[\s*([\\\w]+)::class\s*,\s*(['\"])(\w+)\7\s*\])"
        r"\s*\)(.*?);",
        re.IGNORECASE | re.DOTALL,
    )
    for file in route_files:
        for match in pattern.finditer(file.content):
            legacy_action = match.group(5)
            modern_controller = match.group(6)
            modern_action = match.group(8)
            controller = None
            action = None
            if legacy_action and "@" in legacy_action:
                controller_value, action = legacy_action.rsplit("@", 1)
                controller = controller_value.rsplit("\\", 1)[-1]
            elif modern_controller:
                controller = modern_controller.rsplit("\\", 1)[-1]
                action = modern_action

            chain = match.group(9) or ""
            name_match = re.search(r"->name\s*\(\s*['\"]([^'\"]+)['\"]", chain)
            middleware_matches = re.findall(
                r"->middleware\s*\(\s*(?:\[\s*)?['\"]([^'\"]+)['\"]", chain
            )
            middleware, route_prefix = _route_context(file.content, match.start())
            middleware.extend(middleware_matches)
            raw_path = "/".join(filter(None, [route_prefix.strip("/"), match.group(3).strip("/")]))
            routes.append(
                Route(
                    method=match.group(1).upper(),
                    path=f"/{raw_path}",
                    controller=controller,
                    action=action,
                    name=name_match.group(1) if name_match else None,
                    middleware=list(dict.fromkeys(middleware)),
                    source=SourceRef(
                        file=file.relative_path,
                        line=line_number(file.content, match.start()),
                        confidence="confirmed" if controller and action else "unknown",
                    ),
                )
            )
    return routes
