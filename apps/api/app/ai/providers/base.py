from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TokenUsage:
    """Provider-reported usage without inventing a split the API did not return."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class AIProviderOutputError(RuntimeError):
    """A safe, typed provider outcome that must not become a classification."""

    outcome: str = "failed"

    def __init__(self, reason: str | None = None):
        self.reason = reason
        super().__init__(reason or self.outcome)


class AIProviderIncompleteError(AIProviderOutputError):
    outcome = "incomplete"


class AIProviderRefusalError(AIProviderOutputError):
    outcome = "refusal"


class AIProvider(ABC):
    last_token_usage: int | None = None
    last_usage: TokenUsage = TokenUsage()

    @abstractmethod
    async def extract_structured(self, text: str, schema: dict[str, Any]) -> dict[str, Any]: ...
    @abstractmethod
    async def summarize(self, context: str) -> str: ...
    @abstractmethod
    async def analyze_match(self, context: str) -> dict[str, Any]: ...
