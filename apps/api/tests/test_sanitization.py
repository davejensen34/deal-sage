import json

import pytest

from app.research.ingestion import assert_safe_source_content
from app.research.sanitization import sanitize_external_mapping


def test_obituary_public_facts_survive_while_capability_fields_are_dropped():
    payload = {
        "id": "public-record-1",
        "full_name": "Example Person",
        "state": "CO",
        "date_of_death": "2026-08-31",
        "obituary_url": "https://example.test/obituary/1",
        "edit_token": "must-never-persist",
        "creationSessionId": "must-never-persist-either",
        "internal_note": "unknown-field-value",
    }
    policy = {
        "id": True,
        "full_name": True,
        "state": True,
        "date_of_death": True,
        "obituary_url": True,
    }

    sanitized = sanitize_external_mapping(payload, policy)
    serialized = json.dumps(sanitized.data)
    report = json.dumps(sanitized.report.public_summary())

    assert sanitized.data["full_name"] == "Example Person"
    assert "must-never-persist" not in serialized
    assert "unknown-field-value" not in serialized
    assert sanitized.report.public_summary()["dropped_sensitive_count"] == 2
    assert sanitized.report.public_summary()["dropped_unknown_count"] == 1
    assert "must-never-persist" not in report


def test_nested_allowlist_drops_sensitive_and_unknown_fields():
    sanitized = sanitize_external_mapping(
        {
            "result": {
                "title": "Public title",
                "management_url": "https://example.test/manage/secret",
                "new_provider_field": "not reviewed",
            }
        },
        {"result": {"title": True}},
    )

    assert sanitized.data == {"result": {"title": "Public title"}}
    assert sanitized.report.dropped_sensitive_paths == ("$.result.management_url",)
    assert sanitized.report.dropped_unknown_paths == ("$.result.new_provider_field",)


def test_structured_values_require_explicit_nested_policy():
    with pytest.raises(ValueError, match="Structured allowlist rule"):
        sanitize_external_mapping({"result": {"title": "Public"}}, {"result": True})


def test_persistence_guard_normalizes_field_spelling():
    for field_name in ("edit_token", "editToken", "EDIT-TOKEN", "session_token"):
        with pytest.raises(ValueError, match="Forbidden source field"):
            assert_safe_source_content({field_name: "must-not-land"})
