"""Run with python -m scripts.run_milestone7_analysis from apps/api."""

import argparse
import asyncio
from pathlib import Path

from app.research.analysis_preparation import canonical_bytes
from app.research.analysis_execution import execute, PROTOCOL
from scripts.prepare_milestone7_analysis import prepare


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bundle", "manifest", "database", "evidence-dir", "env-file", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--approved-protocol-id", required=True)
    parser.add_argument("--confirm-live-calls", action="store_true")
    args = parser.parse_args()
    if not args.confirm_live_calls or args.approved_protocol_id != PROTOCOL:
        raise ValueError("Explicit protocol approval is required")
    if canonical_bytes(prepare(args.manifest, args.database, args.evidence_dir)) != args.bundle.read_bytes():
        raise ValueError("Evidence no longer reproduces the frozen requests")
    from app.core.config import Settings
    from openai import AsyncOpenAI
    settings = Settings(_env_file=args.env_file)
    async with AsyncOpenAI(api_key=settings.openai_api_key, max_retries=0, timeout=45) as client:
        result = await execute(args.bundle, args.output, client, args.approved_protocol_id)
    print({"outcomes": [r["status"] for r in result["calls"]],
           "analysis_attempts": sum(r["analysis_attempted"] for r in result["calls"]),
           "count_requests": result["count_requests"], "reserved_cents": result["reserved_cents"]})


if __name__ == "__main__":
    asyncio.run(main())
