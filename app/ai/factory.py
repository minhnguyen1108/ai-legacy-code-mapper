from __future__ import annotations

from pathlib import Path

from app.ai.base import AIProvider, NoAIProvider
from app.ai.ollama_client import OllamaProvider
from app.ai.openai_client import OpenAIProvider


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    import os

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def create_provider(name: str, model: str | None, workspace: Path) -> AIProvider:
    load_env_file(workspace / ".env.local")
    load_env_file(workspace / ".env")
    if name == "openai":
        return OpenAIProvider(model)
    if name == "ollama":
        return OllamaProvider(model)
    return NoAIProvider()
