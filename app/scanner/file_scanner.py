from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SKIP_DIRS = {
    ".git",
    ".idea",
    ".legacy-code-mapper",
    ".vscode",
    "bootstrap/cache",
    "docs/generated",
    "node_modules",
    "storage",
    "vendor",
}


@dataclass
class PhpFile:
    path: Path
    relative_path: str
    content: str


def scan_php_files(root: Path) -> list[PhpFile]:
    files: list[PhpFile] = []
    for path in root.rglob("*.php"):
        relative = path.relative_to(root).as_posix()
        parts = relative.split("/")
        if any(part in SKIP_DIRS for part in parts):
            continue
        if any(relative == item or relative.startswith(f"{item}/") for item in SKIP_DIRS):
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        files.append(PhpFile(path=path, relative_path=relative, content=content))
    return sorted(files, key=lambda item: item.relative_path)
