import json
from typing import Any

from jsonschema import validate

from .base import AIProvider, AIProviderIncompleteError, AIProviderRefusalError, TokenUsage


class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str, model: str, *, max_output_tokens: int = 1000, timeout_seconds: float = 30):
        from anthropic import AsyncAnthropic

        self.client = AsyncAnthropic(api_key=api_key, timeout=timeout_seconds)
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.last_token_usage = None
        self.last_usage = TokenUsage()

    def _capture_usage(self, response: Any) -> None:
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", 0) or 0
        output_tokens = getattr(usage, "output_tokens", 0) or 0
        self.last_usage = TokenUsage(
            input_tokens=input_tokens if usage else None,
            output_tokens=output_tokens if usage else None,
            total_tokens=input_tokens + output_tokens if usage else None,
        )
        self.last_token_usage = self.last_usage.total_tokens

    @staticmethod
    def _ensure_complete(response: Any) -> None:
        stop_reason = getattr(response, "stop_reason", None)
        if stop_reason == "max_tokens":
            raise AIProviderIncompleteError("max_tokens")
        if stop_reason == "refusal" or any(
            getattr(block, "type", None) == "refusal"
            for block in (getattr(response, "content", []) or [])
        ):
            raise AIProviderRefusalError("provider_refusal")

    async def summarize(self, context: str) -> str:
        response = await self.client.messages.create(model=self.model, max_tokens=self.max_output_tokens, messages=[{"role": "user", "content": context}])
        self._capture_usage(response)
        self._ensure_complete(response)
        return "".join(block.text for block in response.content if block.type == "text")

    async def extract_structured(self, text: str, schema: dict[str, Any]) -> dict[str, Any]:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_output_tokens,
            system=(
                "Return only the requested structured result. "
                "Do not add facts absent from the supplied evidence."
            ),
            messages=[{"role": "user", "content": text}],
            # Prompt-only JSON instructions proved insufficient in the bounded
            # cohort; native constrained decoding is the enforceable contract.
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        self._capture_usage(response)
        self._ensure_complete(response)
        raw = "".join(block.text for block in response.content if block.type == "text")
        result = json.loads(raw)
        validate(instance=result, schema=schema)
        return result

    async def analyze_match(self, context: str) -> dict[str, Any]:
        return {"summary": await self.summarize(context)}
