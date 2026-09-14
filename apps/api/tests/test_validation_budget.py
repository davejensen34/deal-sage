import json
import pytest
from app.research.validation_budget import ValidationBudget, PROTOCOL


def test_failures_remain_reserved_and_finished_records_immutable(tmp_path):
    budget = ValidationBudget(tmp_path, PROTOCOL)
    with budget.locked():
        attempt = budget.reserve("search", {"query": "fictional public query"}, label="fixture")
        assert budget.read()["attempts"][0]["status"] == "reserved"
        budget.finish(attempt, {"status": "failed", "error_class": "TimeoutError"})
        with pytest.raises(ValueError):
            budget.finish(attempt, {"status": "completed"})
    assert budget.read()["attempts"][0]["reserved_cents"] == 15


def test_budget_cap_and_concurrent_lock(tmp_path):
    budget = ValidationBudget(tmp_path, PROTOCOL)
    with budget.locked():
        with pytest.raises(FileExistsError):
            with budget.locked():
                pass
        for n in range(33):
            budget.reserve("search", {"query": "fixture"}, label=str(n))
        with pytest.raises(ValueError, match="exhausted"):
            budget.reserve("search", {}, label="over")
    assert sum(r["reserved_cents"] for r in budget.read()["attempts"]) == 495


def test_approval_and_negative_reservation_refused(tmp_path):
    with pytest.raises(ValueError):
        ValidationBudget(tmp_path, "old-approval")
    budget = ValidationBudget(tmp_path, PROTOCOL)
    budget.path.write_text(json.dumps({"protocol": PROTOCOL, "ceiling_cents":500, "attempts":[{"reserved_cents":-1}]}))
    with pytest.raises(ValueError):
        budget.read()


def test_changed_request_cannot_silently_reuse_budget_history(tmp_path):
    budget = ValidationBudget(tmp_path, PROTOCOL)
    with budget.locked():
        budget.reserve("search", {"query": "original"}, label="fixture")
        (tmp_path / "request-001.json").write_bytes(b'{}')
        with pytest.raises(ValueError, match="request changed"):
            budget.reserve("search", {"query": "retry"}, label="retry")
