import json
from typing import Any

from jsonschema import validate

from .base import AIProvider


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str, *, max_output_tokens: int = 1000, timeout_seconds: float = 30):
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds)
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.last_token_usage = None

    def _capture_usage(self, response: Any) -> None:
        usage = getattr(response, "usage", None)
        self.last_token_usage = getattr(usage, "total_tokens", None)

    async def summarize(self, context: str) -> str:
        response = await self.client.responses.create(
            model=self.model,
            input=context,
            max_output_tokens=self.max_output_tokens,
            # Public-record research can contain personal data. Do not retain the
            # response provider-side merely because the API default permits it.
            store=False,
        )
        self._capture_usage(response)
        return response.output_text

    async def extract_structured(self, text: str, schema: dict[str, Any]) -> dict[str, Any]:
        response = await self.client.responses.create(
            model=self.model,
            input=text,
            max_output_tokens=self.max_output_tokens,
            store=False,
            text={"format": {"type": "json_schema", "name": "dealsage_extraction", "schema": schema, "strict": True}},
        )
        self._capture_usage(response)
        result = json.loads(response.output_text)
        validate(instance=result, schema=schema)
        return result

    async def analyze_match(self, context: str) -> dict[str, Any]:
        return {"summary": await self.summarize(context)}
