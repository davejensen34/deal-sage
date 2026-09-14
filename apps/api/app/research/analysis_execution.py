"""One-shot execution of the separately approved, hash-pinned M7 bundle."""

import json
import os
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from jsonschema import ValidationError

from app.ai.providers.openai import OpenAIProvider
from app.ai.providers.base import AIProviderIncompleteError, AIProviderRefusalError
from app.research.analysis_preparation import canonical_bytes, observation_errors
from app.research.ingestion import assert_safe_source_content
from app.research.observation_contract import DIAGNOSTIC_VERSION, safe_diagnostic_codes, assess_observation
from app.research.analysis_revision import PROTOCOL_V3
from app.research.frozen_signal_intake import EXECUTION as PROTOCOL_V4, validate_bundle


# Separately approved September 14 retry. The v1 claim and failed result remain
# immutable; this version grants one new attempt of the same frozen requests.
PROTOCOL = "m7-analysis-execution-v2"
BUNDLE_SHA256 = "5142f997f0f29192f8ca9bd4b47e68b4532ce3e611aa4d1bea5aceecfcaeb08e"
# Prepared for review, not yet approved for live execution. The explicit protocol
# argument must be supplied only after the user approves this new payload/budget.
BUNDLE_V3_SHA256 = "1e0ca8fd29c6d2016560bc81d9009cd429efdcafda8bfe5880baf2786b9fde3d"


def persist(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".tmp")
    with temporary.open("wb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def execution_bundle(payload: bytes, approval: str, approved_bundle_sha256: str | None = None) -> tuple[dict, str]:
    """Validate the entire cohort before claims, reservations or provider calls."""
    expected_hash = {PROTOCOL: BUNDLE_SHA256, PROTOCOL_V3: BUNDLE_V3_SHA256}.get(approval)
    if approval == PROTOCOL_V4:
        expected_hash = approved_bundle_sha256
    if not expected_hash or sha256(payload).hexdigest() != expected_hash:
        raise ValueError("Approval or frozen bundle mismatch")
    return (validate_bundle(payload) if approval == PROTOCOL_V4 else json.loads(payload)), expected_hash


async def execute(bundle_path: Path, output: Path, client, approval: str, *, approved_bundle_sha256: str | None = None) -> dict:
    """Failures consume their reservation; the persistent claim forbids reruns.

    The caller revalidates evidence offline and supplies a no-retry client. No
    database is opened here, and only validated observations survive persistence.
    """
    payload = bundle_path.read_bytes()
    bundle, expected_hash = execution_bundle(payload, approval, approved_bundle_sha256)
    if client.max_retries != 0:
        raise ValueError("Provider retries must be disabled")
    # The location is tied to the approved bundle, not a caller-selected output.
    claim = bundle_path.parent / f".{approval}.claimed"
    with claim.open("x") as stream:
        stream.write(expected_hash)
        stream.flush()
        os.fsync(stream.fileno())
    with output.open("xb"):
        pass
    record = {"protocol": approval, "bundle_sha256": expected_hash,
              "started_at": datetime.now(timezone.utc).isoformat(), "calls": [],
              "count_requests": 0, "reserved_cents": 0, "actual_billed_usd": None}
    if approval == PROTOCOL_V4:
        record.update(intake_sha256=bundle["intake_sha256"], intake_reports=bundle["intake_reports"],
                      cohort_counts=bundle["cohort_counts"])
    persist(output, record)
    for packet in bundle["requests"]:
        row = {"slot": packet["slot"], "request_sha256": packet["request_sha256"],
               "status": "reserved", "reserved_cents": 5, "analysis_attempted": False}
        record["calls"].append(row)
        record["reserved_cents"] += 5
        persist(output, record)
        request = packet["request"]
        if record["reserved_cents"] > 15 or len(record["calls"]) > 3:
            raise ValueError("Execution ceiling exhausted")
        try:
            # Count the full instructions/input/schema before generation. A count
            # endpoint failure aborts the run rather than guessing token usage.
            count_body = {k: request[k] for k in ("model", "input", "instructions", "text", "tools", "truncation")}
            record["count_requests"] += 1
            persist(output, record)
            # The installed SDK requires dictionary type arguments when parsing;
            # a bare dict raises ValueError even for a valid token-count response.
            count = await client.post("/responses/input_tokens", body=count_body, cast_to=dict[str, object])
            tokens = count.get("input_tokens")
            if type(tokens) is int:
                row["counted_input_tokens"] = tokens
            if type(tokens) is not int:
                row["reason"] = "input_count_missing_or_invalid"
                raise ValueError("Input count contract failed")
            if not 0 <= tokens <= 20000:
                row["reason"] = "input_count_outside_limit"
                raise ValueError("Input token ceiling or count contract failed")
            # At reviewed rates, 20k input plus v3's 6k output costs at most
            # $0.017, below five cents without cached-input savings. V2 caps 2k.
            row["analysis_attempted"] = True
            persist(output, record)
            response = await client.responses.create(**request)
            usage = response.usage
            row.update(input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
                       returned_model=response.model,
                       estimated_usd=usage.input_tokens * .25 / 1e6 + usage.output_tokens * 2 / 1e6)
            OpenAIProvider._ensure_complete(response)
            if response.status != "completed" or response.model != request["model"]:
                raise ValueError("Unexpected response status or model")
            observation = json.loads(response.output_text)
            assert_safe_source_content(observation)
            context = json.loads(request["input"])
            sources = {s["source_id"] for s in context["sources"]}
            if approval in {PROTOCOL_V3, PROTOCOL_V4}:
                assessment = assess_observation(observation, sources, context["case_origin"])
                row["observation_contract"] = assessment.contract_version
                if assessment.diagnostic_codes:
                    row.update(status="invalid", reason="observation_validation",
                               diagnostic_version=DIAGNOSTIC_VERSION,
                               diagnostic_codes=assessment.diagnostic_codes)
                else:
                    row.update(status="completed", model_observation=assessment.model_observation,
                               deterministic_research_disposition=assessment.deterministic_research_disposition)
            else:
                errors = observation_errors(observation, sources)
                if errors:
                    row.update(status="invalid", reason="observation_consistency",
                               diagnostic_version=DIAGNOSTIC_VERSION,
                               diagnostic_codes=safe_diagnostic_codes(errors))
                else:
                    row.update(status="completed", observation=observation)
        except AIProviderIncompleteError:
            row.update(status="incomplete")
        except AIProviderRefusalError:
            row.update(status="refusal")
        except (ValidationError, json.JSONDecodeError):
            row.update(status="invalid", reason="observation_schema")
        except Exception as error:
            # Never persist provider errors, response payloads or capability values.
            row.update(status="failed", error_class=type(error).__name__)
        persist(output, record)
        if not row["analysis_attempted"]:
            break
    record["finished_at"] = datetime.now(timezone.utc).isoformat()
    persist(output, record)
    return record
