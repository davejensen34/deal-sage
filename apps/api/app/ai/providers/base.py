from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    @abstractmethod
    async def extract_structured(self, text: str, schema: dict[str, Any]) -> dict[str, Any]: ...
    @abstractmethod
    async def summarize(self, context: str) -> str: ...
    @abstractmethod
    async def analyze_match(self, context: str) -> dict[str, Any]: ...
