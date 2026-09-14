from copy import deepcopy
from datetime import date
from hashlib import sha256
import json

import pytest

from app.research.analysis_preparation import canonical_bytes
from app.research.recent_discovery import MODEL, PROTOCOL, execute, prepare, validate

DAY = date(2026, 9, 14)


def frozen(tmp_path):
    payload = canonical_bytes(prepare(DAY.isoformat()))
    path = tmp_path / "discovery-requests-v1.json"
    path.write_bytes(payload)
    return path, sha256(payload).hexdigest()


def response(sources=None):
    return {"status": "completed", "model": MODEL, "usage": {"input_tokens": 200, "output_tokens": 50},
            "output_text": "MODEL NARRATIVE MUST NOT LAND", "access_token": "DROP ME",
            "output": [{"type": "web_search_call", "action": {"sources": sources or []}}]}


class Client:
    max_retries = 0

    def __init__(self, directory, result):
        self.directory, self.result, self.calls = directory, result, []
        self.responses = self

    async def create(self, **request):
        # An injected provider observes the durable reservation before each call.
        record = json.loads((self.directory / "discovery-results-v1.json").read_bytes())
        assert record["calls"][-1]["status"] == "reserved"
        assert record["reserved_cents"] == 12 * (len(self.calls) + 1)
        assert (self.directory / f".{PROTOCOL}.claimed").exists()
        self.calls.append(request)
        if isinstance(self.result, Exception):
            raise self.result
        return deepcopy(self.result)


def test_frozen_queries_cover_eight_families_without_preknown_names():
    bundle = prepare(DAY.isoformat())
    assert len(bundle["slots"]) == len({s["signal_type"] for s in bundle["slots"]}) == 8
    assert {s["state"] for s in bundle["slots"]} == {"CO", "UT", "TX"}
    assert all("after:2026-06-15 before:2026-09-15" in s["query"] for s in bundle["slots"])
    assert all(s["request"]["store"] is False and s["request"]["max_tool_calls"] == 1 for s in bundle["slots"])
    assert bundle["approval_status"] == "not_authorized"
    assert 8 * bundle["limits"]["reservation_cents_per_request"] <= bundle["limits"]["total_ceiling_cents"]


@pytest.mark.parametrize("change", ["query", "budget", "tool", "date", "model", "slots"])
@pytest.mark.asyncio
async def test_tampering_cannot_reach_provider_even_with_matching_hash(tmp_path, change):
    path, _ = frozen(tmp_path)
    bundle = json.loads(path.read_bytes())
    if change == "query": bundle["slots"][0]["query"] = "Unapproved business"
    if change == "budget": bundle["limits"]["total_ceiling_cents"] = 10000
    if change == "tool": bundle["slots"][0]["request"]["max_tool_calls"] = 8
    if change == "date": bundle["policy"]["lookback_days"] = 3650
    if change == "model": bundle["slots"][0]["request"]["model"] = "substitute"
    if change == "slots": bundle["slots"].append(bundle["slots"][0])
    payload = canonical_bytes(bundle)
    path.write_bytes(payload)
    client = Client(tmp_path, response())
    with pytest.raises(ValueError):
        await execute(path, client, sha256(payload).hexdigest(), PROTOCOL, today=DAY)
    assert not client.calls and not (tmp_path / f".{PROTOCOL}.claimed").exists()


@pytest.mark.parametrize("today", [date(2026, 9, 13), date(2026, 9, 22)])
def test_future_and_expired_assessment_rejected(tmp_path, today):
    path, digest = frozen(tmp_path)
    with pytest.raises(ValueError):
        validate(path.read_bytes(), digest, PROTOCOL, today=today)


def test_new_assessment_cannot_reuse_expired_pricing():
    payload = canonical_bytes(prepare("2026-10-01"))
    with pytest.raises(ValueError, match="pricing"):
        validate(payload, sha256(payload).hexdigest(), PROTOCOL, today=date(2026, 10, 1))


@pytest.mark.asyncio
async def test_empty_searches_are_not_replaced_and_cannot_replay(tmp_path):
    path, digest = frozen(tmp_path)
    client = Client(tmp_path, response())
    record = await execute(path, client, digest, PROTOCOL, today=DAY)
    assert len(client.calls) == 8 and record["reserved_cents"] == 96
    assert record["candidate_count"] == record["source_evidence_count"] == 0
    assert record["eligible_signal_count"] is None and record["unattempted_slots"] == []
    with pytest.raises(ValueError):
        await execute(path, client, digest, PROTOCOL, today=DAY)
    assert len(client.calls) == 8


@pytest.mark.parametrize("failure", ["exception", "missing_usage", "output_limit", "model", "incomplete", "extra_tool"])
@pytest.mark.asyncio
async def test_failure_stops_without_retry_and_preserves_reservation(tmp_path, failure):
    path, digest = frozen(tmp_path)
    result = response()
    if failure == "exception": result = RuntimeError("SECRET PROVIDER ERROR")
    if failure == "missing_usage": result["usage"] = None
    if failure == "output_limit": result["usage"]["output_tokens"] = 1001
    if failure == "model": result["model"] = "unexpected"
    if failure == "incomplete": result["status"] = "incomplete"
    if failure == "extra_tool": result["output"].append(deepcopy(result["output"][0]))
    client = Client(tmp_path, result)
    record = await execute(path, client, digest, PROTOCOL, today=DAY)
    assert len(client.calls) == 1 and record["reserved_cents"] == 12
    assert len(record["unattempted_slots"]) == 7
    assert record["calls"][0]["status"] == "failed"
    assert "SECRET" not in json.dumps(record)


@pytest.mark.asyncio
async def test_candidates_keep_discovery_lineage_without_capabilities_or_narrative(tmp_path):
    path, digest = frozen(tmp_path)
    sources = [{"url": f"https://example.test/{i}", "title": f"Fictional source {i}", "edit_token": "DROP ME"} for i in range(7)]
    client = Client(tmp_path, response(sources))
    record = await execute(path, client, digest, PROTOCOL, today=DAY)
    assert record["candidate_count"] == 40
    candidate = record["calls"][0]["candidates"][0]
    assert candidate["access_observations"]["access_review_required"] is True
    assert "MODEL NARRATIVE" not in json.dumps(record) and "DROP ME" not in json.dumps(record)
    assert record["database_writes"] == record["direct_http_requests"] == 0


@pytest.mark.parametrize("guard", ["approval", "hash", "retries", "existing_output"])
@pytest.mark.asyncio
async def test_preconditions_stop_before_provider(tmp_path, guard):
    path, digest = frozen(tmp_path)
    client = Client(tmp_path, response())
    approval = PROTOCOL
    if guard == "approval": approval = "historical-approval"
    if guard == "hash": digest = "0" * 64
    if guard == "retries": client.max_retries = 2
    if guard == "existing_output": (tmp_path / "discovery-results-v1.json").write_text("preserve")
    with pytest.raises(ValueError):
        await execute(path, client, digest, approval, today=DAY)
    assert not client.calls and not (tmp_path / f".{PROTOCOL}.claimed").exists()


@pytest.mark.asyncio
async def test_real_sdk_uses_frozen_request_with_offline_transport(tmp_path):
    import httpx
    from openai import AsyncOpenAI

    path, digest = frozen(tmp_path)
    calls = []
    def handle(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200, json=response([{"url": "https://example.test/announcement", "title": "Fictional notice"}]))
    async with AsyncOpenAI(api_key="fixture-not-a-credential", max_retries=0,
                           http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle))) as client:
        record = await execute(path, client, digest, PROTOCOL, today=DAY)
    assert calls == [s["request"] for s in prepare(DAY.isoformat())["slots"]]
    assert record["candidate_count"] == 8
    assert all(c["status"] == "completed" for c in record["calls"])


@pytest.mark.parametrize("confirm", [False, True])
@pytest.mark.asyncio
async def test_cli_refuses_missing_approval_before_loading_credentials(tmp_path, monkeypatch, confirm):
    import sys
    from app.core import config
    from scripts.recent_milestone7_discovery import main
    path, digest = frozen(tmp_path)
    def forbidden_settings(*args, **kwargs):
        pytest.fail("Credentials must not be loaded before valid explicit approval")
    monkeypatch.setattr(config, "Settings", forbidden_settings)
    args = ["discovery", "run", "--bundle", str(path), "--env-file", str(tmp_path / "not-read.env"),
            "--approved-protocol-id", PROTOCOL, "--approved-bundle-sha256", "0" * 64 if confirm else digest]
    if confirm: args.append("--confirm-live-calls")
    monkeypatch.setattr(sys, "argv", args)
    with pytest.raises(ValueError):
        await main()
    assert not (tmp_path / f".{PROTOCOL}.claimed").exists()
