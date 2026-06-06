from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from app.ai.base import AIProvider


class OllamaProvider(AIProvider):
    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:7b")
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")

    def complete(self, system: str, prompt: str) -> str:
        payload = json.dumps(
            {
                "model": self.model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError) as error:
            raise RuntimeError(f"Ollama request failed: {error}") from error
        return data.get("message", {}).get("content", "").strip()
