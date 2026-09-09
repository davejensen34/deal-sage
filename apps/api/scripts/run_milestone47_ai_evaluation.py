"""Execute the explicitly approved Milestone 4.7 provider matrix once."""

import argparse
import asyncio
import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.research.milestone47_ai_run import (
    ensure_manifest_claims,
    execute_approved_cohort,
    verify_execution_inputs,
)
from app.storage.local import LocalEvidenceStorage


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--frozen-packets", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--approved-protocol-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--confirm-live-calls", action="store_true")
    return parser.parse_args()


async def main() -> None:
    args = arguments()
    if not args.confirm_live_calls:
        raise ValueError("Live execution requires --confirm-live-calls")
    manifest = json.loads(args.manifest.read_bytes())
    settings = Settings(_env_file=args.env_file)
    engine = create_engine(f"sqlite:///{args.database.resolve()}")
    storage = LocalEvidenceStorage(args.evidence_dir)
    with Session(engine) as db:
        verify_execution_inputs(db, storage, manifest, args.frozen_packets, args.approved_protocol_id)
        claim_ids = ensure_manifest_claims(db, manifest)
        result = await execute_approved_cohort(db, settings, manifest, claim_ids)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("protocol_id", "calls", "search_calls", "estimated_cost_cents")}))


if __name__ == "__main__":
    asyncio.run(main())
