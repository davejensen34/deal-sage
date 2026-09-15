from copy import deepcopy
from hashlib import sha256
import json

import pytest

from app.research import usefulness_feedback as module
from app.research.analysis_preparation import canonical_bytes
from scripts import summarize_milestone7_feedback as cli


@pytest.fixture
def package(monkeypatch):
    raw = canonical_bytes({"items": [{"slot": slot} for slot in ("A", "B", "C")],
                           "result_sha256": "a"*64, "bundle_sha256": "b"*64})
    monkeypatch.setattr(module, "PACKAGE_SHA256", sha256(raw).hexdigest())
    return raw


def feedback(slots=("A",), reviewer="Fictional reviewer", usefulness="useful", seconds=None):
    return dict(version="m7-human-usefulness-v1", package_sha256=module.PACKAGE_SHA256,
                result_sha256="a"*64, bundle_sha256="b"*64, reviewer=reviewer,
                attribution="self_reported_human", recorded_at="2026-09-14T15:00:00.000Z",
                judgments=[dict(slot=s, usefulness=usefulness, rationale="Fictional test judgment",
                                self_reported_review_seconds=seconds) for s in slots],
                unreviewed_slots=sorted(set(("A", "B", "C"))-set(slots)),
                analyst_acceptance=None, time_saved_seconds=None, promotions=0)


def test_no_feedback_is_missing_not_negative(package):
    result = module.summarize_feedback(package, [])
    assert result["packet_review_coverage"] == {"numerator": 0, "denominator": 3, "value": 0}
    assert result["judgment_usefulness"]["value"] is None
    assert result["self_reported_review_seconds"]["known_total"] is None
    assert result["judgments"] == 0 and result["unreviewed_slots"] == ["A", "B", "C"]
    assert result["time_saved_seconds"] is None and result["promotion_precision"] is None
    assert not result["milestone_complete"]


@pytest.mark.parametrize('package_constant', ['COMPLETION_PACKAGE_SHA256', 'TEXAS_PACKAGE_SHA256'])
def test_corrective_cohort_remains_separate_from_prior_feedback(package, monkeypatch, package_constant):
    recent = canonical_bytes({"items": [{"slot": "NEW"}], "result_sha256": "c"*64, "bundle_sha256": "d"*64})
    digest = sha256(recent).hexdigest()
    monkeypatch.setattr(module, package_constant, digest)
    result = module.summarize_feedback(recent, [])
    assert result["package_sha256"] == digest
    assert result["packet_review_coverage"]["denominator"] == 1
    assert result["judgment_usefulness"]["value"] is None
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        module.summarize_feedback(recent, [canonical_bytes(feedback())])


def test_partial_and_multiple_reviewers_keep_distinct_denominators(package):
    first = feedback(seconds=0)
    second = feedback(("A", "B"), reviewer="Second fictional reviewer", usefulness="defer")
    original = deepcopy((first, second))
    raw = [canonical_bytes(first), canonical_bytes(second)]
    result = module.summarize_feedback(package, raw)
    assert (first, second) == original
    assert result["packet_review_coverage"]["value"] == 2/3
    assert result["judgment_usefulness"] == {"numerator": 1, "denominator": 3, "value": 1/3}
    assert result["judgment_counts"] == {"useful": 1, "not_useful": 0, "defer": 2}
    assert result["self_reported_review_seconds"] == {"measured": 1, "missing": 2, "known_total": 0}
    assert result["reviewer_labels"] == 2 and result["unreviewed_slots"] == ["C"]
    assert result["feedback_sha256"] == sorted(sha256(r).hexdigest() for r in raw)
    assert "Fictional test judgment" not in json.dumps(result)
    assert module.summarize_feedback(package, list(reversed(raw))) == result


def test_disjoint_exports_from_one_reviewer_are_counted_once(package):
    result = module.summarize_feedback(package, [canonical_bytes(feedback(("A",), seconds=60)),
                                               canonical_bytes(feedback(("B",), usefulness="not_useful", seconds=90))])
    assert result["reviewer_labels"] == 1 and result["judgments"] == 2
    assert result["self_reported_review_seconds"]["known_total"] == 150


@pytest.mark.parametrize("name", ["Fictional reviewer", " fictional   REVIEWER ", "Ｆictional reviewer"])
def test_duplicate_or_revised_judgment_requires_deliberate_selection(package, name):
    with pytest.raises(ValueError, match="Duplicate reviewer-slot"):
        module.summarize_feedback(package, [canonical_bytes(feedback()), canonical_bytes(feedback(reviewer=name, usefulness="defer"))])


@pytest.mark.parametrize("field,value", [
    ("version", "unrecognized"), ("attribution", "agent_interpretation"), ("reviewer", "  "),
    ("recorded_at", "2026-09-14"), ("recorded_at", "bad date"),
    ("analyst_acceptance", True), ("time_saved_seconds", 100), ("promotions", 1), ("promotions", False),
    ("unexpected_private_detail", "DO-NOT-PRINT"),
    ("package_sha256", "0"*64), ("result_sha256", "0"*64), ("bundle_sha256", "0"*64),
    ("unreviewed_slots", ["B"]), ("unreviewed_slots", ["A", "B", "C"]), ("unreviewed_slots", ["B", "B", "C"]),
])
def test_bad_contract_and_binding_are_refused_safely(package, field, value):
    data = feedback(); data[field] = value
    with pytest.raises(ValueError) as error:
        module.summarize_feedback(package, [canonical_bytes(data)])
    assert "DO-NOT-PRINT" not in str(error.value)


@pytest.mark.parametrize("field,value", [("slot", "unknown"), ("usefulness", "accept"),
    ("rationale", "  "), ("self_reported_review_seconds", -1), ("self_reported_review_seconds", 86401),
    ("self_reported_review_seconds", True), ("self_reported_review_seconds", "60")])
def test_invalid_judgments_cannot_influence_metrics(package, field, value):
    data = feedback(); data["judgments"][0][field] = value
    with pytest.raises(ValueError):
        module.summarize_feedback(package, [canonical_bytes(data)])


def test_duplicate_slots_and_duplicate_json_keys_are_rejected(package):
    data = feedback(); data["judgments"].append(deepcopy(data["judgments"][0]))
    with pytest.raises(ValueError, match="partition"):
        module.summarize_feedback(package, [canonical_bytes(data)])
    raw = canonical_bytes(feedback())
    raw = raw[:-1] + b',"reviewer":"hidden override"}'
    with pytest.raises(ValueError, match="contract"):
        module.summarize_feedback(package, [raw])


def test_unrelated_package_and_oversized_inputs_are_rejected(package):
    with pytest.raises(ValueError, match="Unreviewed"):
        module.summarize_feedback(package+b" ", [])
    with pytest.raises(ValueError, match="contract"):
        module.summarize_feedback(package, [b" "*(module.MAX_BYTES+1)])
    with pytest.raises(ValueError, match="Too many"):
        module.summarize_feedback(package, [b"{}"]*101)


def test_cli_never_overwrites_inputs_or_existing_output(package, tmp_path, monkeypatch):
    source = tmp_path/"package.json"; source.write_bytes(package)
    output = tmp_path/"summary.json"
    monkeypatch.setattr("sys.argv", ["feedback", "--package", str(source), "--output", str(output)])
    cli.main()
    before = output.read_bytes()
    assert json.loads(before)["judgments"] == 0
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2 and output.read_bytes() == before and source.read_bytes() == package
