"""Prepare offline; run only after approval of the exact discovery payload/budget."""

import argparse
import asyncio
from hashlib import sha256
from pathlib import Path

from app.research.analysis_preparation import canonical_bytes
from app.research.recent_discovery import prepare, validate, execute


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    freeze = commands.add_parser("prepare")
    freeze.add_argument("--assessment-date", required=True)
    freeze.add_argument("--output", type=Path, required=True)
    run = commands.add_parser("run")
    run.add_argument("--bundle", type=Path, required=True)
    run.add_argument("--env-file", type=Path, required=True)
    run.add_argument("--approved-protocol-id", required=True)
    run.add_argument("--approved-bundle-sha256", required=True)
    run.add_argument("--confirm-live-calls", action="store_true")
    args = parser.parse_args()
    if args.command == "prepare":
        payload = canonical_bytes(prepare(args.assessment_date))
        with args.output.open("xb") as stream:
            stream.write(payload)
        print({"sha256": sha256(payload).hexdigest(), "approval_status": "not_authorized", "external_calls": 0})
        return
    if not args.confirm_live_calls:
        raise ValueError("Explicit approval is required before live discovery")
    validate(args.bundle.read_bytes(), args.approved_bundle_sha256, args.approved_protocol_id)
    # Validate the complete payload before loading credentials or creating a client.
    from app.core.config import Settings
    from openai import AsyncOpenAI
    settings = Settings(_env_file=args.env_file)
    async with AsyncOpenAI(api_key=settings.openai_api_key, base_url="https://api.openai.com/v1",
                           max_retries=0, timeout=45) as client:
        result = await execute(args.bundle, client, args.approved_bundle_sha256, args.approved_protocol_id)
    print({"outcomes": [c["status"] for c in result["calls"]], "candidates": result["candidate_count"],
           "reserved_cents": result["reserved_cents"], "source_evidence_count": 0})


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as error:
        # Provider errors may include response bodies or credentials; emit no text.
        print({"status": "stopped", "error_class": type(error).__name__})
        raise SystemExit(1) from None
