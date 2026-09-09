"""Retrieve and freeze a zero-provider-call Milestone 4.7 evidence cohort."""

import argparse
import asyncio
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.domain.models import ResearchCase
from app.research.preflight import preflight_case, validate_candidate_manifest
from app.research.retrieval import HttpDocumentProvider
from app.storage.local import LocalEvidenceStorage


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


async def main() -> None:
    args = arguments()
    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    validate_candidate_manifest(manifest)
    args.database.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{args.database.resolve()}")
    Base.metadata.create_all(engine)
    storage = LocalEvidenceStorage(args.evidence_dir)
    cases = []
    with Session(engine) as db:
        existing_cases = db.scalars(select(ResearchCase).order_by(ResearchCase.id)).all()
        for index, case_spec in enumerate(manifest["cases"]):
            case_id, evidence = await preflight_case(
                db,
                storage,
                HttpDocumentProvider(timeout_seconds=20),
                case_spec,
                existing_case=existing_cases[index] if index < len(existing_cases) else None,
            )
            cases.append(
                {
                    "slot": case_spec["slot"],
                    "state": case_spec["state"],
                    "origin": case_spec["origin"],
                    "case_id": case_id,
                    "evidence": [item.__dict__ for item in evidence],
                }
            )
    frozen = {
        "schema_version": "milestone-4-7-frozen-packets-v1",
        "candidate_manifest_hash": sha256(manifest_bytes).hexdigest(),
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "cases": cases,
        "authorization": {"paid_search_calls": 0, "model_calls": 0},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(frozen, indent=2) + "\n")
    print(
        json.dumps(
            {
                "cases": len(cases),
                "evidence_items": sum(len(case["evidence"]) for case in cases),
                "paid_search_calls": 0,
                "model_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
