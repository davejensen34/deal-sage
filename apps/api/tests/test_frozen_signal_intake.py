from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.domain.models import CaseEvidence, EvidenceClaim, RawArtifact, ResearchCase, SourceCandidate
from app.research import analysis_execution as execution
from app.research.analysis_preparation import canonical_bytes, MODEL
from app.research.frozen_signal_intake import EXECUTION, prepare_snapshot, strict_json, validate_bundle
from scripts.prepare_recent_milestone7 import prepare

POLICY = {"version": "signal-intake-v1", "assessment_date": "2026-09-14", "lookback_days": 90}


def cohort(dates=("2026-09-01", "2024-01-01", None)):
    cases = []
    for i, date in enumerate(dates, 1):
        excerpt = f"Fictional company {i}: Jordan retired {date or 'on an unknown date'}."
        cases.append({"case_id": i, "requested_state": "UT", "origin": "hybrid", "policy": dict(POLICY),
            "evidence": [{"id": i, "artifact_id": i, "content_hash": sha256(excerpt.encode()).hexdigest(),
                "canonical_url": f"https://example.test/{i}", "publisher": "Fictional publisher", "source_type": "newspaper",
                "published_at": "2026-09-14T00:00:00", "retrieved_at": "2026-09-14T00:00:00",
                "relevant_excerpt": excerpt, "candidate_id": i, "access_decision": "approved", "access_decided_by": "Fixture reviewer"}],
            "claims": [{"id": i, "evidence_id": i, "subject_type": "person", "status": "asserted",
                "classification": "source_fact", "source_authority": "publisher", "directness": "direct_statement",
                "object_value": {"person": "Jordan", "signal_type": "retirement", "event_status": "reported",
                                 "event_date": date, "event_date_excerpt": excerpt}}],
            "conflicted_claim_ids": []})
    return {"version": "m7-signal-intake-v1", "cases": cases}


class Client:
    max_retries = 0

    def __init__(self, *, failure=False, tokens=100):
        self.responses = self
        self.calls = self.counts = 0
        self.failure, self.tokens = failure, tokens

    async def post(self, *args, **kwargs):
        self.counts += 1
        return {"input_tokens": self.tokens}

    async def create(self, **request):
        self.calls += 1
        if self.failure:
            raise RuntimeError("do not retain this provider body")
        source_id = json.loads(request["input"])["sources"][0]["source_id"]
        observation = dict(case_origin="hybrid", identity_resolution="unresolved", relationship="unclear",
            relationship_time="unclear", operating_status="unknown", contradiction_state="none",
            supported_source_ids=[source_id], contradictions=[], unresolved_questions=["Verify the business"],
            summary="Fictional useful clue", state_fit="unknown", private_company_fit="unknown")
        return SimpleNamespace(status="completed", model=MODEL, output=[],
            usage=SimpleNamespace(input_tokens=100, output_tokens=50), output_text=json.dumps(observation))


def write_bundle(tmp_path, snapshot):
    bundle = prepare_snapshot(snapshot)
    payload = canonical_bytes(bundle)
    path = tmp_path / "bundle.json"
    path.write_bytes(payload)
    return path, sha256(payload).hexdigest(), bundle


def test_freeze_routes_exclusions_and_no_assessment_leakage():
    snapshot = cohort()
    before = deepcopy(snapshot)
    bundle = prepare_snapshot(snapshot)
    assert snapshot == before
    assert bundle["cohort_counts"] == {"considered": 3, "eligible": 1, "excluded": 2}
    assert [r["slot"] for r in bundle["requests"]] == ["M7-RECENT-1"]
    assert bundle["limits"]["reserved_cents_total"] == 5
    assert bundle["intake_reports"][1]["signals"][0]["route"] == "background"
    assert bundle["intake_reports"][2]["signals"][0]["route"] == "date_verification"
    context = json.loads(bundle["requests"][0]["request"]["input"])
    assert set(context) == {"case_origin", "requested_state", "signal_type", "as_of", "sources"}
    assert "intake_reports" not in str(context) and "event_date_excerpt" not in str(context)
    assert validate_bundle(canonical_bytes(bundle)) == bundle


@pytest.mark.asyncio
async def test_only_eligible_packet_consumes_slot_and_history_is_preserved(tmp_path):
    path, fingerprint, bundle = write_bundle(tmp_path, cohort())
    history = tmp_path / f".{execution.PROTOCOL_V3}.claimed"
    history.write_bytes(b"historical claim")
    client = Client()
    result = await execution.execute(path, tmp_path / "out.json", client, EXECUTION, approved_bundle_sha256=fingerprint)
    assert client.counts == client.calls == 1 and result["reserved_cents"] == 5
    assert result["calls"][0]["status"] == "completed"
    assert "model_observation" in result["calls"][0]
    assert result["cohort_counts"] == bundle["cohort_counts"]
    assert result["intake_reports"] == bundle["intake_reports"]
    assert history.read_bytes() == b"historical claim"
    assert sha256(path.read_bytes()).hexdigest() == fingerprint
    with pytest.raises(FileExistsError):
        await execution.execute(path, tmp_path / "retry.json", client, EXECUTION, approved_bundle_sha256=fingerprint)
    assert client.calls == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("dates", [("2024-01-01",), (None,), ("2026-09-01",)])
async def test_empty_or_conflicted_cohort_stops_before_any_reservation(tmp_path, dates):
    snapshot = cohort(dates)
    if dates[0] == "2026-09-01":
        snapshot["cases"][0]["conflicted_claim_ids"] = [1]
    path, fingerprint, _ = write_bundle(tmp_path, snapshot)
    client = Client()
    with pytest.raises(ValueError, match="No eligible recent"):
        await execution.execute(path, tmp_path / "out.json", client, EXECUTION, approved_bundle_sha256=fingerprint)
    assert client.counts == client.calls == 0
    assert not (tmp_path / f".{EXECUTION}.claimed").exists()
    assert not (tmp_path / "out.json").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["route", "request", "limits", "snapshot", "approval"])
async def test_tamper_refused_even_with_matching_hash_argument(tmp_path, field):
    path, fingerprint, data = write_bundle(tmp_path, cohort())
    if field == "route":
        data["intake_reports"][1]["analysis_allowed"] = True
    elif field == "request":
        data["requests"][0]["request"]["tools"] = [{"type": "web_search"}]
    elif field == "limits":
        data["limits"]["reserved_cents_total"] = 500
    elif field == "snapshot":
        data["intake_snapshot"]["cases"][0]["claims"][0]["object_value"]["event_date"] = "2024-01-01"
    else:
        fingerprint = None
    if field != "approval":
        path.write_bytes(canonical_bytes(data))
        fingerprint = sha256(path.read_bytes()).hexdigest()
    client = Client()
    with pytest.raises(ValueError):
        await execution.execute(path, tmp_path / "out.json", client, EXECUTION, approved_bundle_sha256=fingerprint)
    assert client.counts == client.calls == 0
    assert not (tmp_path / f".{EXECUTION}.claimed").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("failure,tokens,calls", [(True, 100, 1), (False, 20001, 0)])
async def test_failed_attempts_keep_budget_and_token_gates(tmp_path, failure, tokens, calls):
    path, fingerprint, _ = write_bundle(tmp_path, cohort())
    client = Client(failure=failure, tokens=tokens)
    result = await execution.execute(path, tmp_path / "out.json", client, EXECUTION, approved_bundle_sha256=fingerprint)
    assert client.calls == calls and client.counts == 1 and result["reserved_cents"] == 5
    assert "do not retain" not in json.dumps(result)


@pytest.mark.parametrize("kind", ["duplicates", "cross_case", "mixed_policy", "too_many", "unsupported_access", "oversize"])
def test_invalid_snapshots(kind):
    snapshot = cohort()
    if kind == "duplicates":
        snapshot["cases"].append(deepcopy(snapshot["cases"][0]))
    elif kind == "cross_case":
        snapshot["cases"][0]["claims"][0]["evidence_id"] = 2
    elif kind == "mixed_policy":
        snapshot["cases"][1]["policy"]["lookback_days"] = 30
    elif kind == "too_many":
        snapshot = cohort(("2026-09-01",) * 4)
    elif kind == "unsupported_access":
        snapshot["cases"][0]["evidence"][0]["access_decision"] = "blocked"
    else:
        snapshot["cases"][0]["evidence"][0]["relevant_excerpt"] *= 1000
    with pytest.raises(ValueError):
        prepare_snapshot(snapshot)


@pytest.mark.parametrize("payload", [b'{"x":1,"x":2}', b'{"x":NaN}', b" " * 2_000_001], ids=["duplicate", "nonfinite", "oversize"])
def test_ambiguous_or_unbounded_json(payload):
    with pytest.raises(ValueError):
        strict_json(payload)


def test_read_only_freeze_verifies_bytes_and_detects_changed_claims(tmp_path):
    path = tmp_path / "fixture.db"
    root = tmp_path / "evidence"
    root.mkdir()
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine)
    snap = cohort(("2026-09-01",))["cases"][0]
    src = snap["evidence"][0]
    raw = src["relevant_excerpt"].encode()
    (root / "source.txt").write_bytes(raw)
    with Session(engine) as db:
        db.add(ResearchCase(id=1, origin_strategy="hybrid", signal_intake_policy=POLICY))
        db.add(SourceCandidate(id=1, case_id=1, canonical_url=src["canonical_url"], domain="example.test",
            likely_source_type="newspaper", relevance_reason="Fixture", proposed_use="case_specific_research",
            search_provider="fixture", access_decision="approved", access_decided_by="Fixture reviewer"))
        db.add(RawArtifact(id=1, content_hash=src["content_hash"], source_key="fixture", canonical_url=src["canonical_url"],
            retrieved_at=datetime(2026, 9, 14), media_type="text/plain", byte_size=len(raw), storage_key="source.txt", contract_fingerprint="a" * 64))
        db.flush()
        db.add(CaseEvidence(id=1, case_id=1, raw_artifact_id=1, content_hash=src["content_hash"], source_mode="case_specific_research",
            canonical_url=src["canonical_url"], publisher=src["publisher"], source_type="newspaper", relevant_excerpt=src["relevant_excerpt"],
            retrieved_at=datetime(2026, 9, 14), provenance={"candidate_id": 1}, classification="source_fact"))
        db.flush()
        db.add(EvidenceClaim(**snap["claims"][0], case_id=1, predicate="transition", confidence=.8))
        db.commit()
    before = path.read_bytes()
    frozen = prepare(path, root, [(1, "UT")])
    assert path.read_bytes() == before and frozen["cohort_counts"]["eligible"] == 1
    assert prepare(path, root, [(1, "UT")]) == frozen
    with Session(engine) as db:
        claim = db.get(EvidenceClaim, 1)
        claim.object_value = claim.object_value | {"event_date": "2024-01-01"}
        db.commit()
    assert prepare(path, root, [(1, "UT")]) != frozen
    (root / "source.txt").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="bytes"):
        prepare(path, root, [(1, "UT")])
    with pytest.raises(Exception):
        prepare(tmp_path / "absent.db", root, [(1, "UT")])
    assert not (tmp_path / "absent.db").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("reason", ["empty", "changed_lineage"])
async def test_cli_revalidates_before_loading_credentials(tmp_path, monkeypatch, reason):
    from scripts import run_milestone7_analysis as runner

    path, fingerprint, data = write_bundle(tmp_path, cohort((None,) if reason == "empty" else ("2026-09-01",)))
    monkeypatch.setattr("sys.argv", ["run", "--bundle", str(path), "--database", str(tmp_path / "db"),
        "--evidence-dir", str(tmp_path), "--env-file", str(tmp_path / "must-not-open.env"),
        "--output", str(tmp_path / "out.json"), "--approved-protocol-id", EXECUTION,
        "--approved-bundle-sha256", fingerprint, "--confirm-live-calls"])
    monkeypatch.setattr(runner, "prepare_recent", lambda *args: {**data, "intake_sha256": "changed"})

    def forbidden(*args, **kwargs):
        pytest.fail("Credentials loaded before intake/lineage gate")

    monkeypatch.setattr("app.core.config.Settings", forbidden)
    with pytest.raises(ValueError, match="No eligible|Evidence no longer"):
        await runner.main()
    assert not (tmp_path / "out.json").exists()
