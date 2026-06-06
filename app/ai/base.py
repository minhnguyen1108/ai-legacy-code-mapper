from __future__ import annotations

from abc import ABC, abstractmethod


class AIProvider(ABC):
    @abstractmethod
    def complete(self, system: str, prompt: str) -> str:
        raise NotImplementedError


class NoAIProvider(AIProvider):
    def complete(self, system: str, prompt: str) -> str:
        return ""
