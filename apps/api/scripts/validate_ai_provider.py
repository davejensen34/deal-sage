"""Make one explicit, synthetic provider call to validate local configuration."""

import argparse
import asyncio
import time

from app.ai.providers.anthropic import AnthropicProvider
from app.ai.providers.openai import OpenAIProvider
from app.core.config import get_settings


async def run() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--confirm-live-call",
        action="store_true",
        help="Acknowledge that this sends one billable request to the configured provider.",
    )
    args = parser.parse_args()
    if not args.confirm_live_call:
        parser.error("pass --confirm-live-call to make the single live request")

    settings = get_settings()
    options = {
        "max_output_tokens": min(settings.ai_max_output_tokens, 100),
        "timeout_seconds": settings.ai_request_timeout_seconds,
    }
    if settings.model_provider == "openai" and settings.openai_api_key:
        provider = OpenAIProvider(settings.openai_api_key, settings.openai_model, **options)
        model = settings.openai_model
    elif settings.model_provider == "anthropic" and settings.anthropic_api_key:
        provider = AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model, **options)
        model = settings.anthropic_model
    else:
        raise SystemExit("Select MODEL_PROVIDER=openai or anthropic and configure its API key.")

    started = time.perf_counter()
    result = await provider.summarize(
        "This is a synthetic DealSage connectivity check with no personal data. "
        "Reply with exactly: provider ready"
    )
    latency_ms = int((time.perf_counter() - started) * 1000)
    if result.strip().lower() != "provider ready":
        raise SystemExit("Provider responded, but the bounded smoke-check output was unexpected.")
    print(
        f"provider={settings.model_provider} model={model} "
        f"tokens={provider.last_token_usage} latency_ms={latency_ms} status=ready"
    )


if __name__ == "__main__":
    asyncio.run(run())
