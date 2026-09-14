"""Analyze a frozen recent packet within the approved completion/retry ledger."""

import argparse
import asyncio
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from app.ai.providers.openai import OpenAIProvider
from app.research.frozen_signal_intake import validate_bundle
from app.research.observation_contract import assess_observation
from app.research.validation_budget import ValidationBudget, PROTOCOL

GUIDANCE_VERSION = "completion-guidance-v2"
GUIDANCE = """
Contract clarification (not expected case answers): relationship_time encodes the
relationship label's timing, not the business transition date. Allowed pairs are:
current_owner: current_at_signal, ended_at_signal, unclear;
former_owner: ended_before_signal, ended_at_signal, unclear;
successor: began_after_signal, current_at_signal, unclear;
non_owner_role: current_at_signal, ended_before_signal, ended_at_signal, unclear;
unclear: unclear; none: not_applicable.
If this vocabulary cannot represent a future management role accurately, use
unclear and preserve its precise planned timing in the summary. Do not relabel a
management successor as an ownership successor to fit the vocabulary.
The relationship label successor means a successor to ownership/control supported
by explicit ownership/control-transfer evidence. An executive appointment alone
must remain non_owner_role; preserve that useful management succession in prose.
Private-company fit requires affirmative source evidence; a named company,
executive role, or absence of a stock ticker alone is insufficient. Use unknown
when the supplied evidence does not establish private status. Preserve which
business each financial figure belongs to, and distinguish targets from actuals.
"""


async def execute(budget, bundle_bytes, slot, client):
    if client.max_retries != 0:
        raise ValueError("Automatic provider retries must be disabled")
    # Regeneration verifies the fixed model/schema/no-tools/size bounds and the
    # deterministic freshness gate, rather than trusting serialized eligibility.
    bundle = validate_bundle(bundle_bytes)
    matches = [row for row in bundle["requests"] if row["slot"] == slot]
    if len(matches) != 1:
        raise ValueError("Select one eligible frozen slot")
    request = deepcopy(matches[0]["request"])
    # New effective requests retain the frozen source context unchanged. The
    # additive contract guidance and exact sent bytes are versioned in the ledger;
    # historical requests/results are never regenerated or overwritten.
    request["instructions"] += GUIDANCE
    context = json.loads(request["input"])
    with budget.locked():
        attempt = budget.reserve("analysis", request, label=slot)
        result = {"status": "failed", "slot": slot, "bundle_sha256": sha256(bundle_bytes).hexdigest(),
                  "guidance_version": GUIDANCE_VERSION,
                  "estimated_usd": None, "analysis_attempted": False}
        try:
            count_body = {k: request[k] for k in ("model", "input", "instructions", "text", "tools", "truncation")}
            count = await client.post("/responses/input_tokens", body=count_body, cast_to=dict[str, object])
            tokens = count.get("input_tokens")
            if type(tokens) is not int or not 0 < tokens <= 20000:
                raise ValueError("Input count exceeds reserved envelope")
            result["counted_input_tokens"] = tokens
            result["analysis_attempted"] = True
            response = await client.responses.create(**request)
            usage = response.usage
            if (type(usage.input_tokens) is not int or type(usage.output_tokens) is not int
                    or not 0 <= usage.input_tokens <= 20000 or not 0 <= usage.output_tokens <= 6000):
                raise ValueError("Unexpected usage")
            result.update(input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
                          estimated_usd=round(usage.input_tokens * .25 / 1e6 + usage.output_tokens * 2 / 1e6, 8))
            OpenAIProvider._ensure_complete(response)
            if response.status != "completed" or response.model != request["model"]:
                raise ValueError("Unexpected response status or model")
            assessment = assess_observation(json.loads(response.output_text),
                {s["source_id"] for s in context["sources"]}, context["case_origin"])
            result.update(status="invalid" if assessment.diagnostic_codes else "completed",
                          diagnostic_codes=assessment.diagnostic_codes,
                          model_observation=assessment.model_observation,
                          deterministic_research_disposition=assessment.deterministic_research_disposition)
        except Exception as error:
            # Preserve the failed attempt and its full reservation, never provider
            # exception bodies. Corrective attempts get new immutable ledger IDs.
            result["error_class"] = type(error).__name__
        budget.finish(attempt, result)
    return {"attempt": attempt, **result}


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--slot", required=True)
    parser.add_argument("--approval", choices=[PROTOCOL], required=True)
    args = parser.parse_args()
    from app.core.config import Settings
    from openai import AsyncOpenAI
    settings = Settings(_env_file=args.env_file)
    async with AsyncOpenAI(api_key=settings.openai_api_key, base_url="https://api.openai.com/v1",
                           max_retries=0, timeout=90) as client:
        result = await execute(ValidationBudget(args.directory, args.approval), args.bundle.read_bytes(), args.slot, client)
    print({k: v for k, v in result.items() if k != "model_observation"})


if __name__ == "__main__":
    asyncio.run(main())
