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
        response = await self.client.responses.create(
            model=self.model,
            input=(
                "Perform one public-web search for the following DealSage research question. "
                "Do not treat search snippets or your narrative as source evidence. Query: "
                f"{query}"
            ),
            tools=[{"type": "web_search"}],
            tool_choice="auto",
            include=["web_search_call.action.sources"],
            max_tool_calls=1,
            max_output_tokens=self.max_output_tokens,
            parallel_tool_calls=False,
            # Research queries may concern identifiable people. The repository's
            # retention policy requires provider-side response storage to stay off.
            store=False,
        )
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
            results.append(
                SearchResult(
                    url=canonical_url,
                    title=title.strip() if isinstance(title, str) and title.strip() else hostname,
                    publisher=hostname,
                    relevance_reason="Consulted by the configured web-search provider for this bounded query.",
                    proposed_use="case_specific_research",
                    access_observations={
                        "provider_consulted": True,
                        "access_review_required": True,
                    },
                )
            )
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
