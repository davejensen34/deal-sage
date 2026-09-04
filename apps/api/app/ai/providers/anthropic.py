from typing import Any
from .base import AIProvider


class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str, model: str):
        from anthropic import AsyncAnthropic
        self.client, self.model = AsyncAnthropic(api_key=api_key), model

    async def summarize(self, context: str) -> str:
        response = await self.client.messages.create(model=self.model, max_tokens=500, messages=[{"role": "user", "content": context}])
        return "".join(block.text for block in response.content if block.type == "text")

    async def extract_structured(self, text: str, schema: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Structured extraction is reserved for Milestone 2")

    async def analyze_match(self, context: str) -> dict[str, Any]:
        return {"summary": await self.summarize(context)}
