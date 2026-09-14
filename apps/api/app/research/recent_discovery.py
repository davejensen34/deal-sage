"""Frozen discovery-only M7 evaluation; no corpus, retrieval or analysis writes."""

from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path

from app.research.analysis_preparation import canonical_bytes
from app.research.ingestion import assert_safe_source_content
from app.research.search_openai import search_request, search_results, _value
from app.research.signal_freshness import dated_query, validate_policy

PROTOCOL = "m7-recent-discovery-v1"
MODEL = "gpt-5-mini-2025-08-07"
SLOTS = (
    ("CO-mortality", "CO", "possible_death", "Colorado business owner obituary company"),
    ("UT-retirement", "UT", "retirement", "Utah business owner retirement announcement"),
    ("UT-succession", "UT", "succession", "Utah family business succession announcement"),
    ("CO-transfer", "CO", "ownership_change", "Colorado privately held business ownership transfer"),
    ("TX-founder", "TX", "founder_exit", "Texas private company founder departure"),
    ("UT-dissolution", "UT", "dissolution", "Utah business dissolution public notice"),
    ("TX-restructuring", "TX", "restructuring", "Texas private company restructuring announcement"),
    ("CO-leadership", "CO", "leadership_change", "Colorado private company leadership change"),
)


def prepare(assessment_date: str) -> dict:
    policy = validate_policy({"version": "signal-intake-v1", "assessment_date": assessment_date, "lookback_days": 90})
    slots = []
    for slot, state, signal, query in SLOTS:
        submitted = dated_query(query, policy)
        request = search_request(submitted, MODEL, 1000)
        slots.append({"slot": slot, "state": state, "signal_type": signal, "origin_strategy": "signal_first",
                      "query": submitted, "request": request, "request_sha256": sha256(canonical_bytes(request)).hexdigest()})
    return {"protocol": PROTOCOL, "approval_status": "not_authorized", "policy": policy,
            "limits": {"search_requests": 8, "results_per_request": 5, "max_retries": 0,
                       "reservation_cents_per_request": 12, "total_ceiling_cents": 100,
                       "timeout_seconds": 45, "direct_http_requests": 0, "registry_requests": 0,
                       "analysis_requests": 0, "database_writes": 0},
            "pricing": {"checked_date": "2026-09-14", "input_usd_per_million": .25,
                        "output_usd_per_million": 2, "web_search_usd_per_call": .01,
                        "input_context_ceiling": 400000}, "slots": slots}


def validate(payload: bytes, approved_sha256: str, approval: str, *, today: date | None = None) -> dict:
    if approval != PROTOCOL or sha256(payload).hexdigest() != approved_sha256:
        raise ValueError("Explicit frozen discovery approval is required")
    if len(payload) > 50000:
        raise ValueError("Discovery bundle is oversized")
    bundle = json.loads(payload)
    if canonical_bytes(prepare(bundle["policy"]["assessment_date"])) != payload:
        raise ValueError("Discovery requests or limits differ from the supported freeze")
    assessed = date.fromisoformat(bundle["policy"]["assessment_date"])
    now = today or datetime.now(timezone.utc).date()
    # Approval is for a current discovery window, never a timeless replay license.
    if not assessed <= now <= assessed + timedelta(days=7):
        raise ValueError("Discovery assessment is future-dated or older than seven days")
    if now > date.fromisoformat(bundle["pricing"]["checked_date"]) + timedelta(days=7):
        raise ValueError("Recheck pricing and prepare a new reviewed protocol")
    return bundle


def persist(path: Path, record: dict) -> None:
    temporary = path.with_suffix(".tmp")
    with temporary.open("xb") as stream:
        stream.write(canonical_bytes(record))
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


async def execute(bundle_path: Path, client, approved_sha256: str, approval: str, *, today: date | None = None) -> dict:
    """Persist a permanent one-shot claim and each reservation before network I/O.

    Any failure stops the run, with no replacement calls or released reservation.
    Only allowlisted discovery references and safe usage survive, never responses.
    Output paths are fixed beside the bundle; changing an output cannot replay it.
    """
    bundle = validate(bundle_path.read_bytes(), approved_sha256, approval, today=today)
    if client.max_retries != 0:
        raise ValueError("Discovery provider retries must be disabled")
    output = bundle_path.parent / "discovery-results-v1.json"
    claim = bundle_path.parent / f".{PROTOCOL}.claimed"
    if output.exists() or output.with_suffix(".tmp").exists():
        raise ValueError("Retain existing discovery output or incomplete write")
    with claim.open("x") as stream:
        stream.write(approved_sha256)
        stream.flush()
        os.fsync(stream.fileno())
    record = {"protocol": PROTOCOL, "bundle_sha256": approved_sha256, "policy": bundle["policy"],
              "started_at": datetime.now(timezone.utc).isoformat(), "calls": [], "reserved_cents": 0,
              "actual_billed_usd": None, "source_evidence_count": 0, "eligible_signal_count": None,
              "candidate_count": 0, "direct_http_requests": 0, "database_writes": 0}
    persist(output, record)
    for slot in bundle["slots"]:
        row = {"slot": slot["slot"], "query": slot["query"], "request_sha256": slot["request_sha256"],
               "state": slot["state"], "signal_type": slot["signal_type"], "status": "reserved",
               "reserved_cents": 12, "candidates": [], "estimated_usd": None}
        if record["reserved_cents"] + 12 > bundle["limits"]["total_ceiling_cents"]:
            raise ValueError("Discovery budget exhausted")
        record["calls"].append(row)
        record["reserved_cents"] += 12
        persist(output, record)
        failure_code = "provider_request_failed"
        try:
            response = await client.responses.create(**slot["request"])
            failure_code = "invalid_response_shape"
            # Keep only bounded contract observations, never provider error text
            # or source content, so failed runs can be diagnosed without replay.
            status = _value(response, "status")
            row["response_status"] = status if isinstance(status, str) and status in {"completed", "incomplete", "failed", "cancelled", "queued", "in_progress"} else "unknown"
            row["model_matches"] = _value(response, "model") == MODEL
            row["search_tool_calls"] = sum(_value(item, "type") == "web_search_call" for item in (_value(response, "output") or []))
            usage = _value(response, "usage")
            inputs, outputs = _value(usage, "input_tokens"), _value(usage, "output_tokens")
            failure_code = "usage_missing_or_out_of_bounds"
            if type(inputs) is not int or type(outputs) is not int or not 0 <= inputs <= 400000 or not 0 <= outputs <= 1000:
                raise ValueError("Unbounded or missing usage")
            row.update(input_tokens=inputs, output_tokens=outputs,
                       estimated_usd=round(inputs * .25 / 1000000 + outputs * 2 / 1000000 + .01, 8))
            failure_code = "unexpected_model"
            if not row["model_matches"]:
                raise ValueError("Unexpected model")
            failure_code = "search_not_completed"
            if row["response_status"] != "completed":
                raise ValueError("Incomplete search")
            failure_code = "unexpected_search_tool_count"
            if row["search_tool_calls"] != 1:
                raise ValueError("Unexpected search-tool call count")
            failure_code = "invalid_consulted_sources"
            candidates = [asdict(result) for result in search_results(response, 5)]
            failure_code = "oversized_discovery_reference"
            if any(len(c["url"]) > 2048 or len(c["title"]) > 1000 for c in candidates):
                raise ValueError("Oversized discovery reference")
            failure_code = "unsafe_discovery_fields"
            assert_safe_source_content(candidates)
            row.update(status="completed", candidates=candidates)
            record["candidate_count"] += len(candidates)
        except Exception as error:
            row.update(status="failed", error_class=type(error).__name__, diagnostic_version="discovery-diagnostics-v1", failure_code=failure_code)
            persist(output, record)
            break
        persist(output, record)
    record["finished_at"] = datetime.now(timezone.utc).isoformat()
    record["unattempted_slots"] = [s["slot"] for s in bundle["slots"][len(record["calls"]):]]
    persist(output, record)
    return record
