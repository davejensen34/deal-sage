from app.domain.models import BusinessRelationship, ResearchStage
from app.domain.research import funnel_counts, owner_readiness


def stage(name: str, status: str = "validated") -> ResearchStage:
    return ResearchStage(trail_id=1,stage_type=name,sequence=1,status=status,confidence=90,detail="test")


def relationship(role: str, confidence: float = .9) -> BusinessRelationship:
    return BusinessRelationship(person_id=1,business_id=1,relationship_type=role,active=True,confidence=confidence,evidence_refs=[])


def test_owner_readiness_requires_explicit_controlling_role():
    stages=[stage("business_identity_validated"),stage("web_presence_validated"),stage("relationship_validated")]
    assert owner_readiness(relationship("owner"),stages)[0] is True
    assert owner_readiness(relationship("registered_agent"),stages)[0] is False
    assert owner_readiness(relationship("officer"),stages)[0] is False
    assert owner_readiness(relationship("founder"),stages)[0] is False


def test_owner_readiness_requires_confidence_and_validated_chain():
    stages=[stage("business_identity_validated"),stage("web_presence_validated","needs_review"),stage("relationship_validated")]
    assert owner_readiness(relationship("owner"),stages)[0] is False
    assert owner_readiness(relationship("owner",.74),[stage("business_identity_validated"),stage("web_presence_validated"),stage("relationship_validated")])[0] is False


def test_funnel_counts_only_persisted_validated_stages():
    result={item["stage"]:item["count"] for item in funnel_counts([stage("business_discovered"),stage("entity_anchored"),stage("entity_anchored","needs_review")])}
    assert result["business_discovered"] == 1
    assert result["entity_anchored"] == 1
    assert result["owner_research_ready"] == 0


def test_research_trail_api_preserves_provenance_and_uncertainty(client):
    response=client.get("/api/research/trails/3")
    assert response.status_code == 200
    data=response.json()
    assert data["business"]["name"] == "Copper Finch Design"
    assert data["owner_research_ready"] is False
    assert any(stage["source"] and stage["source"]["canonical_url"] for stage in data["stages"])
    relationship_stage=next(stage for stage in data["stages"] if stage["type"] == "relationship_validated")
    assert relationship_stage["status"] == "insufficient_evidence"
    assert relationship_stage["missing_evidence"]


def test_research_funnel_uses_actual_seed_state(client):
    data=client.get("/api/research/funnel").json()
    counts={item["stage"]:item["count"] for item in data}
    assert counts["business_discovered"] == 18
    assert 0 < counts["owner_research_ready"] < counts["business_discovered"]
