import asyncio

from sqlalchemy import func, select

from app.auth.service import Identity, current_identity
from app.domain.models import AuditEvent, CaseEvidence, EvidenceClaim, SourceCandidate
from app.main import app
from app.research.cases import ResearchCaseService
from app.research.search import FixtureSearchProvider, SearchResult, SearchService


def setup_case(db, restricted=False):
    case = ResearchCaseService(db).create_case("signal_first", {"max_queries": 1})
    rows = asyncio.run(SearchService(db).execute(case.id, FixtureSearchProvider([
        SearchResult("https://example.test/notice", "Notice", "Unverified clue", "research",
            access_observations={"paywall": restricted})]), "Fictional transition"))
    return case, rows[0]


def test_access_review_permissions_scope_restrictions_and_immutable_audit(client, override_db_session):
    db = override_db_session
    case, source = setup_case(db)
    other, blocked = setup_case(db, restricted=True)
    role = "viewer"
    app.dependency_overrides[current_identity] = lambda: Identity(None,"demo","test",None,"Access reviewer",role=role)
    url = f"/api/research/cases/{case.id}/investigation/sources/{source.id}/access"
    payload = {"decision":"approved","reason":"Reviewed ordinary public access","reviewed_conditions":True}
    try:
        assert client.get(f"/api/research/cases/{case.id}/investigation/sources").status_code == 200
        assert client.post(url,json=payload).status_code == 403
        role = "analyst"
        assert client.post(url,json={**payload,"reviewed_conditions":False}).status_code == 422
        assert client.post(url,json={**payload,"reason":"     "}).status_code == 422
        assert client.post(f"/api/research/cases/{other.id}/investigation/sources/{source.id}/access",json=payload).status_code == 404
        blocked_url = f"/api/research/cases/{other.id}/investigation/sources/{blocked.id}/access"
        assert client.post(blocked_url,json=payload).status_code == 409
        assert client.post(blocked_url,json={**payload,"decision":"blocked"}).status_code == 200
        result = client.post(url,json=payload)
        assert result.status_code == 200 and result.json()["reviewer"] == "Access reviewer"
        assert result.json()["reviewed_at"].endswith(("Z","+00:00"))
        assert client.post(url,json={**payload,"decision":"blocked"}).status_code == 409
        # This session still holds the pre-decision object. The SQL claim must
        # reject even that stale object instead of overwriting the API decision.
        import pytest
        with pytest.raises(ValueError,match="immutable"):
            SearchService(db).decide_access(source.id,decision="blocked",reason="Stale reviewer",decided_by="Other")
        audits = db.scalars(select(AuditEvent).where(AuditEvent.action=="source_access_decided")).all()
        assert sum(a.after_state.get("source_candidate_id")==source.id for a in audits) == 1
        assert db.scalar(select(func.count(CaseEvidence.id)).where(CaseEvidence.case_id==case.id)) == 0
    finally:
        app.dependency_overrides.pop(current_identity,None)


def test_evidence_and_claims_are_case_local_bounded_and_provenance_only(client, override_db_session):
    db = override_db_session
    case, source = setup_case(db)
    other, _ = setup_case(db)
    evidence = ResearchCaseService(db).add_evidence(case.id,source_mode="case_specific_research",
        canonical_url=source.canonical_url,publisher="Fictional source",source_type="other",content=b"Source bytes",
        relevant_excerpt="x"*2000,extracted_facts={},provenance={"private_internal_marker":"excluded"})
    # Defend the read boundary for legacy/direct imports as well as normal writes.
    evidence.relevant_excerpt = "x"*2001
    for n in range(21):
        db.add(EvidenceClaim(case_id=case.id,evidence_id=evidence.id,subject_type="business",predicate="role",
            object_value={"name":f"Claim {n}"},relationship_semantics="executive",confidence=.5,
            classification="source_fact",source_authority="secondary",directness="reported"))
    db.commit()
    base=f"/api/research/cases/{case.id}/investigation"
    body=client.get(base+"/evidence").json()
    assert body["items"][0]["content_hash"]==evidence.content_hash
    assert body["items"][0]["excerpt_truncated"] and len(body["items"][0]["excerpt"])==2000
    assert "private_internal_marker" not in str(body) and "storage_key" not in str(body)
    claims=client.get(base+f"/evidence/{evidence.id}/claims").json()
    assert len(claims["items"])==20 and claims["has_next"]
    assert claims["items"][0]["relationship"]=="executive"
    assert len(client.get(base+f"/evidence/{evidence.id}/claims?page=2").json()["items"])==1
    assert client.get(f"/api/research/cases/{other.id}/investigation/evidence/{evidence.id}/claims").status_code==404
    assert client.get(base+"/sources?page=0").status_code==422


def comparison_evidence(db, case_id, publisher="Fictional publisher", content_hash="a"*64, provenance=None):
    row = CaseEvidence(case_id=case_id, source_mode="case_specific_research",
        canonical_url="https://example.test/fictional", publisher=publisher, source_type="other",
        content_hash=content_hash, classification="source_fact", provenance=provenance or {})
    db.add(row)
    db.commit()
    return row


def test_comparisons_explain_existing_rules_without_writes_or_private_metadata(client, override_db_session):
    from app.domain.models import EvidenceRelationship
    db = override_db_session
    case, _ = setup_case(db)
    first = comparison_evidence(db, case.id, provenance={"syndication_group":"private-marker"})
    peers = [comparison_evidence(db, case.id, publisher="Copy"),
        comparison_evidence(db, case.id, publisher="Syndicator", content_hash="b"*64,
            provenance={"syndication_group":"private-marker", "request_metadata":"never expose"}),
        comparison_evidence(db, case.id, publisher="FICTIONAL PUBLISHER", content_hash="c"*64),
        comparison_evidence(db, case.id, publisher="Other publisher", content_hash="d"*64),
        comparison_evidence(db, case.id, publisher="", content_hash="e"*64)]
    counts = [db.scalar(select(func.count(model.id))) for model in (EvidenceRelationship, AuditEvent)]
    url = f"/api/research/cases/{case.id}/investigation/evidence/{first.id}/comparisons"
    result = client.get(url)
    assert result.status_code == 200
    body = result.json()
    assert [r["evidence_id"] for r in body["items"]] == [p.id for p in peers]
    assert [r["relationship"] for r in body["items"]] == ["duplicate","syndicated","same_publisher","independent","unknown"]
    assert "not been verified" in body["items"][3]["explanation"]
    assert "private-marker" not in result.text and "request_metadata" not in result.text
    assert client.get(url).json() == body
    assert counts == [db.scalar(select(func.count(model.id))) for model in (EvidenceRelationship, AuditEvent)]


def test_comparisons_are_paginated_case_local_and_authenticated(client, override_db_session):
    from fastapi import HTTPException
    db = override_db_session
    case, _ = setup_case(db)
    other, _ = setup_case(db)
    first = comparison_evidence(db, case.id)
    other_evidence = comparison_evidence(db, other.id)
    base = f"/api/research/cases/{case.id}/investigation/evidence"
    url = base + f"/{first.id}/comparisons"
    assert client.get(url).json()["items"] == []
    for n in range(21):
        comparison_evidence(db, case.id, content_hash=f"{n:064x}")
    body = client.get(url).json()
    assert len(body["items"]) == 20 and body["has_next"]
    tail = client.get(url+"?page=2").json()
    assert len(tail["items"]) == 1 and not tail["has_next"]
    assert tail["items"][0]["evidence_id"] not in [r["evidence_id"] for r in body["items"]]
    assert client.get(base+f"/{other_evidence.id}/comparisons").status_code == 404
    assert client.get(url+"?page=0").status_code == 422
    app.dependency_overrides[current_identity] = lambda: Identity(None,"demo","test",None,"Viewer",role="viewer")
    try:
        assert client.get(url).status_code == 200
        def unauthenticated():
            raise HTTPException(401,"Sign in required")
        app.dependency_overrides[current_identity] = unauthenticated
        assert client.get(url).status_code == 401
    finally:
        app.dependency_overrides.pop(current_identity,None)


def test_missing_hashes_and_publishers_do_not_establish_duplicate_or_independent_sources(client, override_db_session):
    db = override_db_session
    case, _ = setup_case(db)
    first = comparison_evidence(db, case.id, publisher="", content_hash="")
    comparison_evidence(db, case.id, publisher="", content_hash="")
    comparison_evidence(db, case.id, publisher="", content_hash="f"*64)
    comparison_evidence(db, case.id, publisher="Known", content_hash="e"*64)
    body = client.get(f"/api/research/cases/{case.id}/investigation/evidence/{first.id}/comparisons").json()
    assert all(row["relationship"] == "unknown" for row in body["items"])
