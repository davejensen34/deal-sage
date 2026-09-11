from dataclasses import FrozenInstanceError

import pytest

from app.core.config import get_settings
from app.domain.transition_policies import transition_policy, transition_policy_catalog


def test_catalog_preserves_subject_and_ownership_boundaries():
    catalog = transition_policy_catalog()
    assert catalog["classification"] == "research_guidance"
    assert len(catalog["policies"]) == 8
    assert transition_policy("dissolution").subject_type == "business"
    assert transition_policy("retirement").subject_type == "person"
    assert "does not prove an ownership exit" in transition_policy("retirement").ownership_limitations[0]
    assert "never automatically imply ownership" in transition_policy("leadership_change").ownership_limitations[0]
    assert "announced or completed" in transition_policy("ownership_change").temporal_questions[0]
    assert "successor" in transition_policy("possible_death").ownership_limitations[0]


@pytest.mark.parametrize("signal_type", ["", "death", "unknown", "estate_transition"])
def test_unknown_types_do_not_inherit_mortality_policy(signal_type):
    with pytest.raises(ValueError, match="Unsupported transition"):
        transition_policy(signal_type)


def test_policy_and_export_cannot_mutate_shared_guidance():
    policy = transition_policy("succession")
    with pytest.raises(FrozenInstanceError):
        policy.label = "Ownership confirmed"
    catalog = transition_policy_catalog()
    catalog["policies"][0]["signal_type"] = "invented"
    catalog["limitations"].clear()
    assert transition_policy_catalog()["policies"][0]["signal_type"] == "possible_death"
    assert transition_policy_catalog()["limitations"]


def test_policy_api_is_read_only_guidance(client):
    response = client.get("/api/research/transition-policies")
    assert response.status_code == 200
    assert response.json()["version"] == "transition-policy-v1"
    assert len(response.json()["policies"]) == 8
    assert client.post("/api/research/transition-policies", json={}).status_code == 405


def test_policy_api_requires_identity_in_oidc_mode(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "auth_mode", "oidc")
    client.cookies.clear()
    assert client.get("/api/research/transition-policies").status_code == 401
