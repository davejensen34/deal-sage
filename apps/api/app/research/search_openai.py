"""OpenAI-hosted web discovery behind DealSage's source-neutral search contract."""

from typing import Any

from app.research.search import SearchProvider, SearchResult, canonicalize_public_url


class OpenAIWebSearchProvider(SearchProvider):
    """Return consulted URLs as candidates, never the model narrative as evidence."""

    key = "openai_web_search"

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        timeout_seconds: float = 30,
        max_output_tokens: int = 300,
    ):
        from openai import AsyncOpenAI

        if not api_key.strip() or not model.strip():
            raise ValueError("OpenAI web search requires an API key and model")
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds)
        self.model = model
        self.max_output_tokens = max_output_tokens

    async def search(self, query: str, max_results: int) -> list[SearchResult]:
        if not 1 <= max_results <= 20:
            raise ValueError("OpenAI web-search result limit is outside its bounds")
        response = await self.client.responses.create(**search_request(query, self.model, self.max_output_tokens))
        return search_results(response, max_results)


def search_request(query: str, model: str, max_output_tokens: int) -> dict:
    """Share the exact provider request with reviewable offline evaluation freezes."""
    return {
        "model": model,
        "input": (
            "Perform one public-web search for the following DealSage research question. "
            "Do not treat search snippets or your narrative as source evidence. Query: "
            f"{query}"
        ),
        "tools": [{"type": "web_search"}],
        "tool_choice": "auto",
        "include": ["web_search_call.action.sources"],
        "max_tool_calls": 1,
        "max_output_tokens": max_output_tokens,
        "parallel_tool_calls": False,
        # Research queries can identify people; do not retain provider responses.
        "store": False,
    }


def search_results(response: Any, max_results: int) -> list[SearchResult]:
    """Allowlisted discovery references only; model narrative is never evidence."""
    if not 1 <= max_results <= 20:
        raise ValueError("OpenAI web-search result limit is outside its bounds")
    sources = _response_sources(response)
    if sources is None:
        raise ValueError("OpenAI response did not contain a web-search call")
    results: list[SearchResult] = []
    seen: set[str] = set()
    for source in sources:
        url = _value(source, "url")
        if not isinstance(url, str):
            continue
        try:
            canonical_url, hostname = canonicalize_public_url(url)
        except ValueError:
            continue
        if canonical_url in seen:
            continue
        seen.add(canonical_url)
        title = _value(source, "title")
        results.append(SearchResult(
            url=canonical_url,
            title=title.strip() if isinstance(title, str) and title.strip() else hostname,
            publisher=hostname,
            relevance_reason="Consulted by the configured web-search provider for this bounded query.",
            proposed_use="case_specific_research",
            access_observations={"provider_consulted": True, "access_review_required": True},
        ))
        if len(results) == max_results:
            break
    return results


def _response_sources(response: Any) -> list[Any] | None:
    """Read SDK objects or fixture dictionaries without persisting response text."""
    for item in _value(response, "output") or []:
        if _value(item, "type") != "web_search_call":
            continue
        action = _value(item, "action")
        sources = _value(action, "sources") if action is not None else None
        if sources is not None:
            return list(sources)
    return None


def _value(value: Any, field: str) -> Any:
    return value.get(field) if isinstance(value, dict) else getattr(value, field, None)
