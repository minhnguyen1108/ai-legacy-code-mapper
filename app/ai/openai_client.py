from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from app.ai.base import AIProvider


class OpenAIProvider(AIProvider):
    def __init__(self, model: str | None = None) -> None:
        self.api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is missing. Configure it in .env.local or the environment.")
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-5-mini")

    def complete(self, system: str, prompt: str) -> str:
        payload = json.dumps(
            {
                "model": self.model,
                "input": [
                    {"role": "system", "content": [{"type": "input_text", "text": system}]},
                    {"role": "user", "content": [{"type": "input_text", "text": prompt}]},
                ],
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"OpenAI request failed ({error.code}): {detail}") from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"Could not reach OpenAI: {error.reason}") from error
        text = data.get("output_text")
        if text:
            return text.strip()
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    return content["text"].strip()
        return ""
