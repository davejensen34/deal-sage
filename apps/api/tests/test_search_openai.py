from types import SimpleNamespace

import pytest

from app.research.search_openai import OpenAIWebSearchProvider
from app.core.config import Settings


class AsyncCreate:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def provider(response):
    create = AsyncCreate(response)
    instance = OpenAIWebSearchProvider.__new__(OpenAIWebSearchProvider)
    instance.client = SimpleNamespace(responses=SimpleNamespace(create=create.create))
    instance.model = "test-search-model"
    instance.max_output_tokens = 123
    return instance, create


@pytest.mark.asyncio
async def test_openai_search_maps_only_consulted_sources_and_is_bounded():
    response = SimpleNamespace(
        output_text="A model-authored narrative that must not become evidence.",
        output=[
            SimpleNamespace(
                type="web_search_call",
                action=SimpleNamespace(
                    sources=[
                        SimpleNamespace(url="https://public.example.test/notices/1", title="Notice one"),
                        SimpleNamespace(url="https://public.example.test/notices/1#duplicate", title="Duplicate"),
                        SimpleNamespace(url="javascript:alert(1)", title="Unsafe"),
                        SimpleNamespace(url="https://records.example.test/entity/2", title="Entity two"),
                    ]
                ),
            )
        ],
    )
    search, create = provider(response)

    results = await search.search("Colorado transition notices", max_results=2)

    assert [item.url for item in results] == [
        "https://public.example.test/notices/1",
        "https://records.example.test/entity/2",
    ]
    assert all(item.access_observations["access_review_required"] for item in results)
    assert "model-authored narrative" not in str(results)
    call = create.calls[0]
    assert call["tools"] == [{"type": "web_search"}]
    assert call["include"] == ["web_search_call.action.sources"]
    assert call["max_tool_calls"] == 1
    assert call["max_output_tokens"] == 123
    assert call["parallel_tool_calls"] is False
    assert call["store"] is False


@pytest.mark.asyncio
async def test_openai_search_accepts_dictionary_sdk_shapes():
    search, _ = provider(
        {
            "output": [
                {
                    "type": "web_search_call",
                    "action": {
                        "sources": [
                            {"url": "https://agency.example.test/record", "title": "Agency record"}
                        ]
                    },
                }
            ]
        }
    )

    results = await search.search("fictional record", max_results=1)

    assert results[0].publisher == "agency.example.test"
    assert results[0].title == "Agency record"


@pytest.mark.asyncio
async def test_openai_search_requires_an_observed_search_call():
    search, _ = provider(SimpleNamespace(output=[], output_text="Unsupported answer"))

    with pytest.raises(ValueError, match="did not contain a web-search call"):
        await search.search("question", max_results=1)


def test_web_search_configuration_is_disabled_and_bounded_by_default():
    settings = Settings()

    assert settings.web_search_provider == "disabled"
    assert settings.build_search_provider() is None
    with pytest.raises(ValueError, match="OPENAI_API_KEY is missing"):
        Settings(web_search_provider="openai", openai_api_key=None).build_search_provider()
