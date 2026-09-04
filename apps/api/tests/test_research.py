import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from app.research.experiment import classify_record, summarize
from app.research.sources.colorado import ColoradoBusinessEntitiesAdapter


FIXTURE_PATH = Path(__file__).parent / "fixtures/colorado_records.json"


def fixture_records() -> list[dict]:
    return json.loads(FIXTURE_PATH.read_text())


def test_colorado_query_is_bounded_and_reproducible():
    query = ColoradoBusinessEntitiesAdapter.query(50)
    assert query["$limit"] == "50"
    assert query["$order"] == "entityid ASC"
    with pytest.raises(ValueError):
        ColoradoBusinessEntitiesAdapter.query(101)


@pytest.mark.asyncio
async def test_adapter_normalizes_only_contract_fields():
    payload = [{**fixture_records()[0], "untrusted_extra": "ignore me"}]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        records = await ColoradoBusinessEntitiesAdapter(client).fetch_sample(1)
    assert records[0].source_record_id == "20240000001"
    assert "untrusted_extra" not in records[0].raw
    assert records[0].canonical_url.endswith("fileId=20240000001")


def test_registered_agent_is_never_classified_as_owner():
    now = datetime.now(timezone.utc)
    records = [ColoradoBusinessEntitiesAdapter._normalize_transport(raw, now) for raw in fixture_records()]
    observations = [classify_record(record) for record in records]
    assert {item.ownership_classification for item in observations} == {"unknown"}
    assert observations[0].observed_role == "registered_agent"
    assert observations[2].observed_role == "unknown"


def test_summary_reports_negative_owner_yield():
    now = datetime.now(timezone.utc)
    records = [ColoradoBusinessEntitiesAdapter._normalize_transport(raw, now) for raw in fixture_records()]
    result = summarize(records, 12)
    assert result["metrics"]["owner_controller_evidence_yield_percent"] == 0
    assert result["metrics"]["ownership_unknown_percent"] == 100
    assert result["recommendation"]["decision"] == "change"


def test_research_api_exposes_source_and_aggregate_result(client):
    sources = client.get("/api/research/sources")
    assert sources.status_code == 200
    assert sources.json()[0]["key"] == "colorado_business_entities"
    result = client.get("/api/research/experiments/colorado-owner-discovery")
    assert result.status_code == 200
    assert "observations" not in result.json()
