"""Validate explicitly selected local feedback exports without changing them."""

import argparse
from pathlib import Path

from app.research.analysis_preparation import canonical_bytes
from app.research.usefulness_feedback import MAX_BYTES, summarize_feedback


def read_bounded(path: Path) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Review file exceeds size limit")
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--feedback", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if len(args.feedback) > 100:
        parser.exit(2, "Too many feedback files\n")
    try:
        report = summarize_feedback(read_bounded(args.package), [read_bounded(p) for p in args.feedback])
        with args.output.open("xb") as stream:
            stream.write(canonical_bytes(report))
    except (ValueError, OSError) as error:
        # Paths or OS details may contain private reviewer names. Print only the
        # owned validation messages; source records remain in explicit files.
        message = str(error) if isinstance(error, ValueError) else "Unable to read inputs or create a new output"
        parser.exit(2, message + "\n")
    print({"judgments": report["judgments"], "coverage": report["packet_review_coverage"], "external_calls": 0})


if __name__ == "__main__":
    main()
