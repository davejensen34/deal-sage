from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.ai.providers.anthropic import AnthropicProvider
from app.ai.providers.openai import OpenAIProvider
from app.core.config import Settings


class AsyncCreate:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def openai_provider(response) -> tuple[OpenAIProvider, AsyncCreate]:
    create = AsyncCreate(response)
    provider = OpenAIProvider.__new__(OpenAIProvider)
    provider.client = SimpleNamespace(responses=SimpleNamespace(create=create.create))
    provider.model = "test-openai"
    provider.max_output_tokens = 321
    provider.last_token_usage = None
    return provider, create


def anthropic_provider(response) -> tuple[AnthropicProvider, AsyncCreate]:
    create = AsyncCreate(response)
    provider = AnthropicProvider.__new__(AnthropicProvider)
    provider.client = SimpleNamespace(messages=SimpleNamespace(create=create.create))
    provider.model = "test-anthropic"
    provider.max_output_tokens = 321
    provider.last_token_usage = None
    return provider, create


@pytest.mark.asyncio
async def test_openai_summary_is_bounded_and_disables_storage():
    provider, create = openai_provider(SimpleNamespace(output_text="bounded", usage=SimpleNamespace(total_tokens=17)))

    assert await provider.summarize("public evidence") == "bounded"
    assert create.calls == [{"model": "test-openai", "input": "public evidence", "max_output_tokens": 321, "store": False}]
    assert provider.last_token_usage == 17


@pytest.mark.asyncio
async def test_openai_structured_extraction_validates_schema():
    provider, create = openai_provider(SimpleNamespace(output_text='{"relationship":"owner"}', usage=None))
    schema = {
        "type": "object",
        "properties": {"relationship": {"type": "string", "enum": ["owner", "former_owner"]}},
        "required": ["relationship"],
        "additionalProperties": False,
    }

    assert await provider.extract_structured("evidence packet", schema) == {"relationship": "owner"}
    assert create.calls[0]["store"] is False
    assert create.calls[0]["text"]["format"]["strict"] is True


@pytest.mark.asyncio
async def test_anthropic_summary_is_bounded_and_captures_usage():
    response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="bounded")],
        usage=SimpleNamespace(input_tokens=12, output_tokens=5),
    )
    provider, create = anthropic_provider(response)

    assert await provider.summarize("public evidence") == "bounded"
    assert create.calls[0]["max_tokens"] == 321
    assert provider.last_token_usage == 17


@pytest.mark.asyncio
async def test_anthropic_structured_extraction_rejects_non_json_wrapping():
    response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text='```json\n{"relationship":"owner"}\n```')],
        usage=None,
    )
    provider, _ = anthropic_provider(response)
    schema = {"type": "object", "properties": {"relationship": {"type": "string"}}}

    with pytest.raises(ValueError):
        await provider.extract_structured("evidence packet", schema)


def test_provider_side_response_storage_cannot_be_enabled():
    with pytest.raises(ValidationError, match="provider-side AI response storage must remain disabled"):
        Settings(ai_store_provider_responses=True)
