import json
from typing import Any

from jsonschema import validate

from .base import AIProvider, AIProviderIncompleteError, AIProviderRefusalError, TokenUsage


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str, *, max_output_tokens: int = 1000, timeout_seconds: float = 30):
        from openai import AsyncOpenAI

        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds)
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.last_token_usage = None
        self.last_usage = TokenUsage()

    def _capture_usage(self, response: Any) -> None:
        usage = getattr(response, "usage", None)
        self.last_usage = TokenUsage(
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
            total_tokens=getattr(usage, "total_tokens", None),
        )
        self.last_token_usage = self.last_usage.total_tokens

    @staticmethod
    def _ensure_complete(response: Any) -> None:
        if getattr(response, "status", None) == "incomplete":
            details = getattr(response, "incomplete_details", None)
            raise AIProviderIncompleteError(getattr(details, "reason", None))
        for item in getattr(response, "output", []) or []:
            for block in getattr(item, "content", []) or []:
                if getattr(block, "type", None) == "refusal":
                    raise AIProviderRefusalError(getattr(block, "refusal", None))

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
        self._ensure_complete(response)
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
        self._ensure_complete(response)
        result = json.loads(response.output_text)
        validate(instance=result, schema=schema)
        return result

    async def analyze_match(self, context: str) -> dict[str, Any]:
        return {"summary": await self.summarize(context)}
