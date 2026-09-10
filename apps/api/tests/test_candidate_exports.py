import csv
import io
import json


def test_json_export_preserves_provenance_and_redacts_retained_content(client):
    response = client.post("/api/exports/candidates", json={"format": "json", "state": "CO", "min_confidence": 60, "limit": 2})
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "dealsage-candidate-export-v1"
    assert payload["record_count"] <= 2
    assert all(value is False for value in payload["content_boundaries"].values())
    serialized = json.dumps(payload["records"])
    assert "extracted_text" not in serialized
    assert "normalized_facts" not in serialized
    assert "analyst_notes" not in serialized
    for record in payload["records"]:
        assert record["business"]["state"] == "CO"
        assert record["relationship"]["classification"] == "source_reported_role"
        assert record["score"]["method_version"] == "candidate-score-v1"
        assert record["score"]["interpretation"] == "deterministic_prioritization_not_source_fact"
        assert record["evidence_references"][0]["source"]["canonical_url"].startswith("https://")
        assert record["freshness"]["newest_evidence_retrieved_at"]


def test_csv_export_is_versioned_bounded_and_audited(client):
    response = client.post("/api/exports/candidates", json={"format": "csv", "q": "Alder", "limit": 1})
    assert response.status_code == 200
    assert response.headers["x-dealsage-schema-version"] == "dealsage-candidate-export-v1"
    assert response.headers["x-dealsage-record-count"] == "1"
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert len(rows) == 1
    assert rows[0]["business_name"] == "Alder Ridge Toolworks"
    assert rows[0]["score_method_version"] == "candidate-score-v1"
    assert rows[0]["relationship_classification"] == "source_reported_role"
    detail = client.get(f"/api/candidates/{rows[0]['candidate_id']}").json()
    assert any(event["action"] == "candidate_exported" for event in detail["audit"])


def test_export_rejects_unbounded_or_unknown_inputs(client):
    assert client.post("/api/exports/candidates", json={"limit": 101}).status_code == 422
    assert client.post("/api/exports/candidates", json={"format": "xml"}).status_code == 422
    assert client.post("/api/exports/candidates", json={"state": "Colorado"}).status_code == 422
