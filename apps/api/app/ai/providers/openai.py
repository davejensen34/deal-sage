from typing import Any
from .base import AIProvider


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str):
        from openai import AsyncOpenAI
        self.client, self.model = AsyncOpenAI(api_key=api_key), model

    async def summarize(self, context: str) -> str:
        response = await self.client.responses.create(model=self.model, input=context)
        return response.output_text

    async def extract_structured(self, text: str, schema: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Structured extraction is reserved for Milestone 2")

    async def analyze_match(self, context: str) -> dict[str, Any]:
        return {"summary": await self.summarize(context)}
