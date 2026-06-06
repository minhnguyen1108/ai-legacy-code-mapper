from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.scanner.file_scanner import PhpFile


@dataclass
class MethodInfo:
    name: str
    parameters: str
    visibility: str
    line: int
    body: str


@dataclass
class ClassInfo:
    name: str
    namespace: str
    parent: str | None
    file: PhpFile
    line: int
    methods: dict[str, MethodInfo] = field(default_factory=dict)
    imports: dict[str, str] = field(default_factory=dict)
    property_types: dict[str, str] = field(default_factory=dict)


def line_number(content: str, index: int) -> int:
    return content.count("\n", 0, index) + 1


def _matching_brace(content: str, opening: int) -> int:
    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(opening, len(content)):
        char = content[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    return len(content)


def parse_class(file: PhpFile) -> ClassInfo | None:
    namespace_match = re.search(r"\bnamespace\s+([^;]+);", file.content)
    class_match = re.search(
        r"\b(?:abstract\s+|final\s+)?class\s+(\w+)(?:\s+extends\s+([\\\w]+))?",
        file.content,
    )
    if not class_match:
        return None

    imports: dict[str, str] = {}
    for match in re.finditer(r"^\s*use\s+([^;{]+);", file.content, re.MULTILINE):
        full_name = match.group(1).strip()
        if "," not in full_name:
            imports[full_name.rsplit("\\", 1)[-1]] = full_name

    methods: dict[str, MethodInfo] = {}
    method_pattern = re.compile(
        r"\b(public|protected|private)?\s*(?:static\s+)?function\s+(\w+)\s*\((.*?)\)"
        r"(?:\s*:\s*[?\\\w|]+)?\s*\{",
        re.DOTALL,
    )
    for match in method_pattern.finditer(file.content):
        opening = match.end() - 1
        closing = _matching_brace(file.content, opening)
        methods[match.group(2)] = MethodInfo(
            name=match.group(2),
            parameters=" ".join(match.group(3).split()),
            visibility=match.group(1) or "public",
            line=line_number(file.content, match.start()),
            body=file.content[opening + 1 : closing],
        )

    class_info = ClassInfo(
        name=class_match.group(1),
        namespace=namespace_match.group(1).strip() if namespace_match else "",
        parent=class_match.group(2).rsplit("\\", 1)[-1] if class_match.group(2) else None,
        file=file,
        line=line_number(file.content, class_match.start()),
        methods=methods,
        imports=imports,
    )
    class_info.property_types = infer_property_types(class_info)
    return class_info


def infer_property_types(class_info: ClassInfo) -> dict[str, str]:
    result: dict[str, str] = {}
    constructor = class_info.methods.get("__construct")
    if not constructor:
        return result

    parameter_types: dict[str, str] = {}
    parameter_pattern = re.compile(r"(?:\??([\\\w]+)\s+)?\$(\w+)")
    for match in parameter_pattern.finditer(constructor.parameters):
        if match.group(1):
            parameter_types[match.group(2)] = match.group(1).rsplit("\\", 1)[-1]

    for match in re.finditer(r"\$this->(\w+)\s*=\s*\$(\w+)", constructor.body):
        property_name, parameter_name = match.groups()
        if parameter_name in parameter_types:
            result[property_name] = parameter_types[parameter_name]
    return result
