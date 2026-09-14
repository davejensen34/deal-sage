"""Run with python -m scripts.run_milestone7_analysis from apps/api."""

import argparse
import asyncio
from pathlib import Path

from app.research.analysis_preparation import canonical_bytes
from app.research.analysis_execution import execute, execution_bundle, PROTOCOL, PROTOCOL_V4
from app.research.analysis_revision import PROTOCOL_V3
from scripts.prepare_milestone7_analysis import prepare
from scripts.prepare_recent_milestone7 import prepare as prepare_recent


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bundle", "database", "evidence-dir", "env-file", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--approved-protocol-id", required=True)
    parser.add_argument("--approved-bundle-sha256")
    parser.add_argument("--confirm-live-calls", action="store_true")
    args = parser.parse_args()
    if not args.confirm_live_calls or args.approved_protocol_id not in {PROTOCOL, PROTOCOL_V3, PROTOCOL_V4}:
        raise ValueError("Explicit protocol approval is required")
    payload = args.bundle.read_bytes()
    frozen, _ = execution_bundle(payload, args.approved_protocol_id, args.approved_bundle_sha256)
    version = "v2" if args.approved_protocol_id == PROTOCOL_V3 else "v1"
    if args.approved_protocol_id == PROTOCOL_V4:
        selections = [(case["case_id"], case["requested_state"]) for case in frozen["intake_snapshot"]["cases"]]
        reproduced = prepare_recent(args.database, args.evidence_dir, selections)
    else:
        if args.manifest is None:
            raise ValueError("Historical protocols require their retained manifest")
        reproduced = prepare(args.manifest, args.database, args.evidence_dir, observation_version=version)
    if canonical_bytes(reproduced) != payload:
        raise ValueError("Evidence no longer reproduces the frozen requests")
    from app.core.config import Settings
    from openai import AsyncOpenAI
    settings = Settings(_env_file=args.env_file)
    timeout = 90 if args.approved_protocol_id in {PROTOCOL_V3, PROTOCOL_V4} else 45
    async with AsyncOpenAI(api_key=settings.openai_api_key, max_retries=0, timeout=timeout) as client:
        result = await execute(args.bundle, args.output, client, args.approved_protocol_id,
                               approved_bundle_sha256=args.approved_bundle_sha256)
    print({"outcomes": [r["status"] for r in result["calls"]],
           "analysis_attempts": sum(r["analysis_attempted"] for r in result["calls"]),
           "count_requests": result["count_requests"], "reserved_cents": result["reserved_cents"]})


if __name__ == "__main__":
    asyncio.run(main())
