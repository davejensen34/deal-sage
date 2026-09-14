"""Operate within the explicitly approved $5 M7 completion envelope."""

import argparse
import asyncio
from dataclasses import asdict
from pathlib import Path

from app.research.validation_budget import ValidationBudget, PROTOCOL
from app.research.search_openai import search_request, search_results, _value
from app.research.recent_discovery import MODEL


def candidate_clues(response):
    """A truncated narrative can still return usable, untrusted search references."""
    status = _value(response, "status")
    reason = _value(_value(response, "incomplete_details"), "reason")
    if _value(response, "model") != MODEL or not (
        status == "completed" or status == "incomplete" and reason == "max_output_tokens"
    ):
        raise ValueError("Search response cannot supply retained clues")
    return [asdict(r) for r in search_results(response, 5)]


async def search(args):
    if not 1 <= len(args.query) <= 500 or not 1000 <= args.max_output <= 6000:
        raise ValueError("Search bounds exceeded")
    request = search_request(args.query, MODEL, args.max_output)
    budget = ValidationBudget(args.directory, args.approval)
    with budget.locked():
        attempt = budget.reserve("search", request, label=args.label)
        result = {"status": "failed", "candidates": [], "estimated_usd": None}
        try:
            from app.core.config import Settings
            from openai import AsyncOpenAI
            settings = Settings(_env_file=args.env_file)
            async with AsyncOpenAI(api_key=settings.openai_api_key, base_url="https://api.openai.com/v1", max_retries=0, timeout=60) as client:
                response = await client.responses.create(**request)
            status = _value(response, "status")
            result["response_status"] = status if isinstance(status, str) and status in {"completed", "incomplete", "failed"} else "unknown"
            result["model_matches"] = _value(response, "model") == MODEL
            details = _value(response, "incomplete_details")
            reason = _value(details, "reason")
            result["incomplete_reason"] = reason if isinstance(reason, str) and reason in {"max_output_tokens", "content_filter", "max_tool_calls"} else None
            items = _value(response, "output") or []
            result["output_types"] = [str(_value(i, "type"))[:40] for i in items]
            result["search_actions"] = [str(_value(_value(i, "action"), "type"))[:40] for i in items if _value(i, "type") == "web_search_call"]
            usage = _value(response, "usage")
            inputs, outputs = _value(usage, "input_tokens"), _value(usage, "output_tokens")
            if type(inputs) is int and type(outputs) is int and 0 <= inputs <= 400000 and 0 <= outputs <= args.max_output:
                result.update(input_tokens=inputs, output_tokens=outputs,
                              estimated_usd=round(inputs*.25/1000000+outputs*2/1000000+len(result["search_actions"])*.01, 8))
            else:
                raise ValueError("Invalid usage")
            # Incomplete narrative generation does not invalidate returned search
            # references. They remain untrusted discovery clues, never evidence.
            candidates = candidate_clues(response)
            result.update(status="completed" if result["response_status"] == "completed" else "partial",
                          candidates=candidates)
        except Exception as error:
            result["error_class"] = type(error).__name__
        budget.finish(attempt, result)
        print({"attempt": attempt, **result})


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--approval", choices=[PROTOCOL], required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--max-output", type=int, default=1000)
    await search(parser.parse_args())


if __name__ == "__main__":
    asyncio.run(main())
