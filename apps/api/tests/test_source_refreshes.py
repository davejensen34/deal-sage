from datetime import datetime, timezone

from app.api import routes
from app.research.landing import CuratedSubject
from app.research.refresh import RefreshSource
from app.research.sources.base import SourceAdapter, SourceDefinition, SourceRecord


DEFINITION = SourceDefinition(
    key="colorado_business_entities",
    name="Fixture Colorado",
    jurisdiction="Colorado",
    source_type="government_open_dataset",
    publisher="Fixture publisher",
    landing_url="https://example.test/data",
    api_url="https://example.test/api",
    access_method="Fixture",
    license="Fixture",
    expected_refresh="Daily",
    role_value="Entity identity only",
    limitations=("No ownership inference.",),
)


class SuccessfulAdapter(SourceAdapter):
    definition = DEFINITION

    async def fetch_sample(self, limit: int):
        return [SourceRecord("co-1", "https://example.test/record/1", datetime.now(timezone.utc), {"id": "co-1", "name": "Fixture Co"})]


class FailedAdapter(SourceAdapter):
    definition = DEFINITION

    async def fetch_sample(self, limit: int):
        raise RuntimeError("provider response must not be persisted")


def parser(content: bytes):
    return [CuratedSubject("co:1", "business", {"legal_name": "Fixture Co"}, {"legal_name": "$.name"})]


def test_explicit_refresh_persists_bounded_success(client, monkeypatch, tmp_path):
    monkeypatch.setattr(routes, "refresh_sources", lambda: {DEFINITION.key: RefreshSource(SuccessfulAdapter(), parser, "fixture-v1")})
    monkeypatch.setattr(routes.settings, "evidence_storage_path", tmp_path)

    response = client.post("/api/research/source-refreshes", json={"source_key": DEFINITION.key, "record_limit": 1, "approved_cost_usd": 0})
    assert response.status_code == 201
    refresh = response.json()
    assert refresh["status"] == "succeeded"
    assert refresh["result_summary"]["retrieved"] == 1
    assert refresh["actual_cost_usd"] == 0
    assert refresh["acquisition_run_id"] is not None
    assert refresh["freshness_status"] == "not_measurable_from_record"
    assert client.get("/api/research/source-refreshes").json()[0]["id"] == refresh["id"]


def test_refresh_failure_is_safe_and_durable(client, monkeypatch, tmp_path):
    monkeypatch.setattr(routes, "refresh_sources", lambda: {DEFINITION.key: RefreshSource(FailedAdapter(), parser, "fixture-v1")})
    monkeypatch.setattr(routes.settings, "evidence_storage_path", tmp_path)

    response = client.post("/api/research/source-refreshes", json={"source_key": DEFINITION.key, "record_limit": 1})
    assert response.status_code == 201
    refresh = response.json()
    assert refresh["status"] == "failed"
    assert refresh["error_code"] == "RuntimeError"
    assert "provider response" not in str(refresh)
    assert refresh["freshness_status"] == "refresh_failed"


def test_refresh_contract_enforces_source_and_limit(client):
    assert client.post("/api/research/source-refreshes", json={"source_key": "utah_business_entity_list", "record_limit": 25}).status_code == 422
    assert client.post("/api/research/source-refreshes", json={"source_key": DEFINITION.key, "record_limit": 101}).status_code == 422
