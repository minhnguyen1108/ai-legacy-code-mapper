from __future__ import annotations

import shutil
import subprocess
import tempfile
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass
class SourceProject:
    path: Path
    temporary: bool = False
    _temp_dir: tempfile.TemporaryDirectory[str] | None = None

    def cleanup(self) -> None:
        if self._temp_dir:
            self._temp_dir.cleanup()


def is_git_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "ssh", "git"} or value.startswith("git@")


def resolve_source(value: str) -> SourceProject:
    if not is_git_url(value):
        # Accept a common Windows typo such as ".D:\projects\legacy-app".
        if re.match(r"^\.[A-Za-z]:[\\/]", value):
            value = value[1:]
        path = Path(value).expanduser().resolve()
        if not path.is_dir():
            raise ValueError(f"Project path does not exist or is not a directory: {path}")
        return SourceProject(path=path)

    if shutil.which("git") is None:
        raise RuntimeError("Git is required to analyze a repository URL.")

    temp_dir = tempfile.TemporaryDirectory(prefix="legacy-code-mapper-")
    destination = Path(temp_dir.name) / "repository"
    result = subprocess.run(
        ["git", "clone", "--depth", "1", value, str(destination)],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if result.returncode != 0:
        temp_dir.cleanup()
        detail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "unknown error"
        raise RuntimeError(f"Could not clone repository: {detail}")
    return SourceProject(path=destination, temporary=True, _temp_dir=temp_dir)
