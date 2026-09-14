"""Offline review of the exact retained v3 run; no credentials or database."""

import argparse
from datetime import date
from hashlib import sha256
import json
from pathlib import Path

from app.research.analysis_preparation import canonical_bytes
from app.research.observation_context import contextualize


RESULT_SHA256 = "906a5ba69502ad4edf5ba4291938a8de59d3e2537d882ca7712d6e6fd8375799"
BUNDLE_SHA256 = "1e0ca8fd29c6d2016560bc81d9009cd429efdcafda8bfe5880baf2786b9fde3d"

# Agent interpretations of the frozen source text, not new source facts or human
# decisions. Dates denote evidence available in the announcement, not its later
# scheduled transition date. Premier's contact address is not an operating map.
REVIEWS = {
    "M7-UT-2": ("2024-06-03", "15", "dateline", "UT"),
    "M7-TX-1": ("2025-05-08", "16", "operating_presence", "TX"),
    "M7-CO-3": ("2026-01-09", "17", "address", "NC"),
}


def review(result_bytes: bytes, bundle_bytes: bytes) -> dict:
    if sha256(result_bytes).hexdigest() != RESULT_SHA256 or sha256(bundle_bytes).hexdigest() != BUNDLE_SHA256:
        raise ValueError("Unreviewed evaluation bytes")
    result, bundle = json.loads(result_bytes), json.loads(bundle_bytes)
    packets = {p["slot"]: p for p in bundle["requests"]}
    rows = []
    for call in result["calls"]:
        packet = packets[call["slot"]]
        source_context = json.loads(packet["request"]["input"])
        supported, citation, basis, state = REVIEWS[call["slot"]]
        context = dict(reviewer="DealSage coding agent", review_kind="agent_interpretation",
                       operating_supported_on=supported, operating_source_ids=[citation],
                       geography_basis=basis, geography_state=state, geography_source_ids=[citation])
        row = contextualize(call["model_observation"], {s["source_id"] for s in source_context["sources"]},
                            source_context["case_origin"], as_of=date.fromisoformat(source_context["as_of"]),
                            requested_state=source_context["requested_state"], context=context)
        rows.append({"slot": call["slot"], **row})
    return {"result_sha256": RESULT_SHA256, "bundle_sha256": BUNDLE_SHA256, "reviews": rows,
            "human_usefulness": None, "external_calls": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("result", "bundle", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    report = review(args.result.read_bytes(), args.bundle.read_bytes())
    with args.output.open("xb") as stream:
        stream.write(canonical_bytes(report))
    print({"reviewed": len(report["reviews"]), "external_calls": 0})


if __name__ == "__main__":
    main()
