import pytest

from app.research.cases import ResearchCaseService
from app.research.identity_resolution import IdentityResolutionService, normalize_identity


def evidence_and_claim(db, case_id, *, suffix, predicate, value, content=None, provenance=None, publisher="Publisher One"):
    cases = ResearchCaseService(db)
    text = content or f"Evidence {suffix}"
    evidence = cases.add_evidence(
        case_id,
        source_mode="case_specific_research",
        canonical_url=f"https://example.test/{suffix}",
        publisher=publisher,
        source_type="obituary",
        content=text.encode(),
        relevant_excerpt=text,
        extracted_facts={},
        provenance=provenance or {},
    )
    claim = cases.add_claim(
        case_id,
        evidence.id,
        subject_type="identity",
        predicate=predicate,
        object_value={"value": value},
        relationship_semantics="owner" if predicate == "relationship" else None,
        confidence=0.8,
        classification="source_fact",
        source_authority="publisher",
        directness="direct_statement",
    )
    return evidence, claim


def test_alias_normalization_retains_original_and_claim_provenance(override_db_session):
    case = ResearchCaseService(override_db_session).create_case("signal_first")
    _, claim = evidence_and_claim(
        override_db_session, case.id, suffix="alias", predicate="alias", value="José A. Peña"
    )
    alias = IdentityResolutionService(override_db_session).add_alias(
        case.id,
        entity_type="person",
        canonical_value="Jose Pena",
        alias_value="José A. Peña",
        source_claim_id=claim.id,
    )
    assert alias.alias_value == "José A. Peña"
    assert alias.normalized_value == "jose a pena"
    assert alias.source_claim_id == claim.id
    assert normalize_identity("ACME, L.L.C.") == normalize_identity("Acme LLC")


@pytest.mark.parametrize("direction", ["person_to_business", "business_to_person", "hybrid"])
def test_both_directions_use_one_reviewable_resolution(override_db_session, direction):
    case = ResearchCaseService(override_db_session).create_case("hybrid")
    _, name = evidence_and_claim(
        override_db_session, case.id, suffix=f"name-{direction}", predicate="identity_name", value="Jordan Lee"
    )
    _, geography = evidence_and_claim(
        override_db_session, case.id, suffix=f"geo-{direction}", predicate="state", value="CO"
    )
    resolution = IdentityResolutionService(override_db_session).propose(
        case.id,
        direction=direction,
        subject_value="Jordan Lee",
        candidate_value="Summit Tool Works",
        supporting_claim_ids=[name.id, geography.id],
    )
    assert resolution.direction == direction
    assert resolution.status == "proposed"
    assert resolution.support_dimensions == ["geography", "identity_name"]


def test_name_only_resolution_is_rejected(override_db_session):
    case = ResearchCaseService(override_db_session).create_case("business_first")
    _, name = evidence_and_claim(
        override_db_session, case.id, suffix="name", predicate="legal_name", value="Example Works"
    )
    with pytest.raises(ValueError, match="Name-only"):
        IdentityResolutionService(override_db_session).propose(
            case.id,
            direction="business_to_person",
            subject_value="Example Works",
            candidate_value="Jordan Lee",
            supporting_claim_ids=[name.id],
        )


def test_contradictions_preserve_both_claims(override_db_session):
    case = ResearchCaseService(override_db_session).create_case("signal_first")
    _, current = evidence_and_claim(
        override_db_session, case.id, suffix="current", predicate="relationship", value="owner"
    )
    _, former = evidence_and_claim(
        override_db_session, case.id, suffix="former", predicate="timeline", value="sold in 2018"
    )
    conflict = IdentityResolutionService(override_db_session).record_contradiction(
        case.id,
        current.id,
        former.id,
        contradiction_type="relationship",
        rationale="One source says current owner while another records a prior sale.",
    )
    assert {conflict.left_claim_id, conflict.right_claim_id} == {current.id, former.id}
    assert current.status == "asserted"
    assert former.status == "asserted"


def test_duplicate_syndicated_and_independent_evidence_are_distinct(override_db_session):
    case = ResearchCaseService(override_db_session).create_case("signal_first")
    first, _ = evidence_and_claim(
        override_db_session, case.id, suffix="first", predicate="state", value="CO", content="same copy"
    )
    duplicate, _ = evidence_and_claim(
        override_db_session, case.id, suffix="duplicate", predicate="state", value="CO", content="same copy"
    )
    syndicated, _ = evidence_and_claim(
        override_db_session,
        case.id,
        suffix="syndicated",
        predicate="state",
        value="CO",
        content="edited copy",
        provenance={"syndication_group": "story-123"},
        publisher="Publisher Two",
    )
    syndicated_peer, _ = evidence_and_claim(
        override_db_session,
        case.id,
        suffix="syndicated-peer",
        predicate="state",
        value="CO",
        content="another edit",
        provenance={"syndication_group": "story-123"},
        publisher="Publisher Three",
    )
    independent, _ = evidence_and_claim(
        override_db_session,
        case.id,
        suffix="independent",
        predicate="state",
        value="CO",
        content="official filing",
        publisher="State Registry",
    )
    service = IdentityResolutionService(override_db_session)
    assert service.classify_evidence_pair(case.id, first.id, duplicate.id).relationship_type == "duplicate"
    assert service.classify_evidence_pair(case.id, syndicated.id, syndicated_peer.id).relationship_type == "syndicated"
    assert service.classify_evidence_pair(case.id, first.id, independent.id).relationship_type == "independent"


def test_cross_case_resolution_references_are_rejected(override_db_session):
    cases = ResearchCaseService(override_db_session)
    first = cases.create_case("signal_first")
    second = cases.create_case("business_first")
    _, claim = evidence_and_claim(
        override_db_session, first.id, suffix="cross", predicate="state", value="TX"
    )
    with pytest.raises(ValueError, match="same research case"):
        IdentityResolutionService(override_db_session).propose(
            second.id,
            direction="business_to_person",
            subject_value="Example LLC",
            candidate_value="Taylor Morgan",
            supporting_claim_ids=[claim.id],
        )
