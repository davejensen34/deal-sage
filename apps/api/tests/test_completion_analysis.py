import json
from types import SimpleNamespace

import pytest

from app.research.analysis_preparation import canonical_bytes, MODEL
from app.research.frozen_signal_intake import prepare_snapshot
from app.research.validation_budget import ValidationBudget, PROTOCOL
from scripts.milestone7_completion_analysis import execute
from test_frozen_signal_intake import cohort


class Client:
    max_retries = 0

    def __init__(self, failure=False):
        self.responses = self
        self.failure = failure
        self.calls = 0

    async def post(self, *args, **kwargs):
        return {"input_tokens": 200}

    async def create(self, **request):
        self.calls += 1
        if self.failure:
            raise RuntimeError("private provider failure text")
        output = dict(case_origin="hybrid", identity_resolution="unresolved", relationship="unclear",
            relationship_time="unclear", operating_status="unknown", contradiction_state="none",
            supported_source_ids=["1"], contradictions=[], unresolved_questions=["Verify the business"],
            summary="A useful unverified business clue", state_fit="unknown", private_company_fit="unknown")
        return SimpleNamespace(status="completed", model=MODEL, output=[],
            usage=SimpleNamespace(input_tokens=200, output_tokens=100), output_text=json.dumps(output))


@pytest.mark.asyncio
async def test_failed_attempt_can_be_corrected_without_erasing_or_refunding_it(tmp_path):
    bundle = canonical_bytes(prepare_snapshot(cohort()))
    budget = ValidationBudget(tmp_path, PROTOCOL)
    first = await execute(budget, bundle, "M7-RECENT-1", Client(True))
    second = await execute(budget, bundle, "M7-RECENT-1", Client())
    assert first["status"] == "failed" and first["analysis_attempted"]
    assert second["status"] == "completed"
    assert second["deterministic_research_disposition"] == "needs_more_research"
    assert sum(r["reserved_cents"] for r in budget.read()["attempts"]) == 10
    assert "private provider" not in (tmp_path / "result-001.json").read_text()


@pytest.mark.asyncio
async def test_stale_or_tampered_packet_never_spends(tmp_path):
    budget, client = ValidationBudget(tmp_path, PROTOCOL), Client()
    stale = canonical_bytes(prepare_snapshot(cohort(("2024-01-01",))))
    with pytest.raises(ValueError):
        await execute(budget, stale, "M7-RECENT-1", client)
    bundle = prepare_snapshot(cohort())
    bundle["requests"][0]["request"]["tools"] = [{"type": "web_search"}]
    with pytest.raises(ValueError):
        await execute(budget, canonical_bytes(bundle), "M7-RECENT-1", client)
    assert client.calls == 0 and budget.read()["attempts"] == []
