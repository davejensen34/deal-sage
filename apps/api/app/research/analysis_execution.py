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


PROTOCOL = "m7-analysis-execution-v1"
BUNDLE_SHA256 = "5142f997f0f29192f8ca9bd4b47e68b4532ce3e611aa4d1bea5aceecfcaeb08e"


def persist(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".tmp")
    with temporary.open("wb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


async def execute(bundle_path: Path, output: Path, client, approval: str) -> dict:
    """Failures consume their reservation; the persistent claim forbids reruns.

    The caller revalidates evidence offline and supplies a no-retry client. No
    database is opened here, and only validated observations survive persistence.
    """
    payload = bundle_path.read_bytes()
    if approval != PROTOCOL or sha256(payload).hexdigest() != BUNDLE_SHA256:
        raise ValueError("Approval or frozen bundle mismatch")
    if client.max_retries != 0:
        raise ValueError("Provider retries must be disabled")
    bundle = json.loads(payload)
    # The location is tied to the approved bundle, not a caller-selected output.
    claim = bundle_path.parent / f".{PROTOCOL}.claimed"
    with claim.open("x") as stream:
        stream.write(BUNDLE_SHA256)
        stream.flush()
        os.fsync(stream.fileno())
    with output.open("xb"):
        pass
    record = {"protocol": PROTOCOL, "bundle_sha256": BUNDLE_SHA256,
              "started_at": datetime.now(timezone.utc).isoformat(), "calls": [],
              "count_requests": 0, "reserved_cents": 0, "actual_billed_usd": None}
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
            # 20k input at $0.25/M plus 2k output at $2/M is $0.009,
            # below the five-cent reservation even without cached-input savings.
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
            sources = {s["source_id"] for s in json.loads(request["input"])["sources"]}
            errors = observation_errors(observation, sources)
            if errors:
                row.update(status="invalid", reason="observation_consistency")
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
