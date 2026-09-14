"""Freeze configured recent-signal cases using read-only SQLite and retained bytes."""

import argparse
from hashlib import sha256
from pathlib import Path
import sqlite3

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.research.analysis_preparation import canonical_bytes
from app.research.frozen_signal_intake import freeze_cases
from scripts.prepare_milestone7_analysis import contained_file


def prepare(database: Path, evidence_dir: Path, selections: list[tuple[int, str]]) -> dict:
    def connect():
        connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
        connection.execute("PRAGMA query_only=ON")
        return connection

    engine = create_engine("sqlite://", creator=connect)
    try:
        with Session(engine) as db:
            return freeze_cases(db, selections, lambda key: contained_file(evidence_dir, key).read_bytes())
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--case", action="append", required=True, help="Case ID and target state, e.g. 21:UT")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    selections = []
    for value in args.case:
        case_id, state = value.split(":")
        selections.append((int(case_id), state))
    bundle = prepare(args.database, args.evidence_dir, selections)
    payload = canonical_bytes(bundle)
    with args.output.open("xb") as stream:
        stream.write(payload)
    print({"cohort_counts": bundle["cohort_counts"], "sha256": sha256(payload).hexdigest(),
           "approval_status": "not_authorized", "external_calls": 0})


if __name__ == "__main__":
    main()
