"""Generous pilot budgets catch regressions without pretending to model production load."""

from datetime import datetime, timezone
import json
from time import perf_counter

from app.api import routes
from app.research.landing import CuratedSubject
from app.research.refresh import RefreshSource
from app.research.sources.base import SourceAdapter, SourceDefinition, SourceRecord


class FixtureAdapter(SourceAdapter):
    definition = SourceDefinition(key="colorado_business_entities",name="Performance fixture",jurisdiction="Colorado",source_type="government_open_dataset",publisher="Fixture",landing_url="https://example.test",api_url="https://example.test/api",access_method="fixture",license="fixture",expected_refresh="fixture",role_value="entity",limitations=("No ownership.",))

    async def fetch_sample(self, limit: int):
        return [SourceRecord("perf-1","https://example.test/1",datetime.now(timezone.utc),{"name":"Fixture"})]


def parser(_content: bytes):
    return [CuratedSubject("perf:1","business",{"legal_name":"Fixture"},{"legal_name":"$.name"})]


def duration_ms(action):
    started = perf_counter()
    response = action()
    assert response.status_code < 400
    return (perf_counter() - started) * 1000


def test_representative_pilot_operations_stay_within_budgets(client, monkeypatch, tmp_path):
    monkeypatch.setattr(routes,"refresh_sources",lambda:{FixtureAdapter.definition.key:RefreshSource(FixtureAdapter(),parser,"perf-v1")})
    monkeypatch.setattr(routes.settings,"evidence_storage_path",tmp_path)
    operations = {
        "queue": (lambda: client.get("/api/candidates?page_size=100"), 250),
        "detail": (lambda: client.get("/api/candidates/1"), 250),
        "research": (lambda: client.get("/api/research/workflow-effectiveness"), 500),
        "export": (lambda: client.post("/api/exports/candidates",json={"format":"json","limit":100}), 500),
        "fixture_refresh": (lambda: client.post("/api/research/source-refreshes",json={"source_key":"colorado_business_entities","record_limit":1}), 1000),
    }
    observed = {name:max(duration_ms(action) for _ in range(5)) for name,(action,_budget) in operations.items()}
    print(json.dumps({name:round(value,1) for name,value in observed.items()}, sort_keys=True))
    for name, measured in observed.items():
        assert measured < operations[name][1], f"{name} took {measured:.1f}ms; budget is {operations[name][1]}ms"
