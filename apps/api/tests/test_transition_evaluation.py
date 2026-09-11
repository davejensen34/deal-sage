from pathlib import Path
import json
import socket

import pytest

from app.research.transition_evaluation import Observation, run_cohort, summarize

COHORT = Path(__file__).parent / "fixtures/milestone7_transition_cohort_v1.json"


def row(slot, expected, outcome, **kwargs):
    return Observation(slot=slot, signal_type="retirement", expected_promotion=expected, outcome=outcome, **kwargs)


def test_metrics_keep_failed_and_missing_measurements_explicit():
    result = summarize([
        row("tp",True,"promoted",external_cost_cents=3,human_disposition="useful",analyst_minutes=2),
        row("fp",False,"promoted",external_cost_cents=2,human_disposition="defer"),
        row("fn",True,"abstained",publication_age_days=10),
        row("tn",False,"abstained",publication_age_days=20),
        row("failed",True,"failed"),
    ])
    assert result["promotion_precision"] == {"numerator":1,"denominator":2,"value":0.5}
    assert result["positive_recall"]["value"] == 0.5
    assert result["fixture_agreement"]["denominator"] == 4
    assert result["failed"] == 1
    assert result["promotion_coverage"]["value"] == 0.4
    assert result["abstention"]["value"] == 0.4
    assert result["publication_age_days"] == {"measured":2,"missing":3,"mean":15}
    assert result["external_cost_cents"] == {"measured":2,"missing":3,"known_total":5,"complete":False}
    assert result["analyst_usefulness"]["value"] == 0.5
    assert result["analyst_minutes"] == {"measured":1,"total":2}


def test_empty_denominators_are_unavailable_not_perfect_or_zero():
    result = summarize([])
    for key in ("promotion_precision","positive_recall","fixture_agreement","promotion_coverage","abstention","analyst_usefulness"):
        assert result[key]["value"] is None
    assert result["external_cost_cents"]["known_total"] is None
    assert result["analyst_minutes"]["total"] is None
    assert summarize([row("negative",False,"abstained")])["promotion_precision"]["value"] is None


def test_duplicate_slots_cannot_inflate_metrics():
    with pytest.raises(ValueError,match="unique"):
        summarize([row("same",True,"promoted"),row("same",True,"promoted")])


def test_frozen_cohort_runs_real_bridge_without_network(monkeypatch):
    def network_forbidden(*args, **kwargs):
        raise AssertionError("Offline evaluation attempted network access")
    monkeypatch.setattr(socket.socket,"connect",network_forbidden)
    result = run_cohort(COHORT)
    assert result["offline_contract_passed"] is True
    assert result["live_precision_validated"] is False
    assert result["source_coverage_validated"] is False
    assert result["aggregate"]["slots"] == 64
    assert result["aggregate"]["outcomes"] == {"promoted":16,"abstained":48}
    assert result["aggregate"]["human_review_coverage"]["numerator"] == 0
    assert result["aggregate"]["analyst_usefulness"]["value"] is None
    assert result["aggregate"]["external_cost_cents"]["known_total"] == 0
    assert len(result["by_signal"]) == 8
    assert all(s["promotion_precision"] == {"numerator":2,"denominator":2,"value":1} for s in result["by_signal"].values())


def test_always_promoting_cannot_pass_offline_gate(monkeypatch):
    from app.research.review_queue import ResearchReviewQueueService
    monkeypatch.setattr(ResearchReviewQueueService,"promote",lambda *args,**kwargs: None)
    result = run_cohort(COHORT)
    assert result["offline_contract_passed"] is False
    assert result["aggregate"]["promotion_precision"]["value"] == 0.25


def test_cohort_drift_requires_review(tmp_path):
    changed = json.loads(COHORT.read_text())
    changed["cases"].pop()
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError,match="Frozen cohort changed"):
        run_cohort(path)


def test_cohort_fingerprint_is_portable_across_line_endings(tmp_path):
    path = tmp_path / "windows.json"
    path.write_bytes(COHORT.read_bytes().replace(b"\r\n",b"\n").replace(b"\n",b"\r\n"))
    assert run_cohort(path)["offline_contract_passed"] is True
