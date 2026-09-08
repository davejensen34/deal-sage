from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select

from app.domain.models import CaseEvidence, RawArtifact
from app.research.cases import ResearchCaseService
from app.research.retrieval import (
    CandidateRetrievalService,
    FixtureDocumentProvider,
    RetrievedDocument,
    assert_public_network_url,
)
from app.research.search import FixtureSearchProvider, SearchResult, SearchService
from app.storage.local import LocalEvidenceStorage


async def candidate(db, *, observations=None):
    case = ResearchCaseService(db).create_case(
        "signal_first", {"max_queries": 1, "max_documents": 1}
    )
    results = await SearchService(db).execute(
        case.id,
        FixtureSearchProvider(
            [
                SearchResult(
                    url="https://public.example.test/notice/1",
                    title="Fictional public notice",
                    relevance_reason="May resolve a transition identity.",
                    proposed_use="identity_corroboration",
                    publisher="Fictional Public Notices",
                    likely_source_type="probate_public_notice",
                    geography={"state": "CO"},
                    access_observations=observations or {"authentication_required": False},
                )
            ]
        ),
        "Colorado public transition notices",
        max_results=1,
    )
    return case, results[0]


@pytest.mark.asyncio
async def test_approved_candidate_lands_raw_artifact_before_case_evidence(
    override_db_session, tmp_path
):
    case, source_candidate = await candidate(override_db_session)
    SearchService(override_db_session).decide_access(
        source_candidate.id,
        decision="approved",
        reason="Public page reviewed for bounded case-specific retrieval.",
        decided_by="analyst@example.test",
    )
    document = RetrievedDocument(
        url=source_candidate.canonical_url,
        content=b"Fictional public notice identifying a possible business clue.",
        media_type="text/plain",
        retrieved_at=datetime.now(timezone.utc),
    )

    evidence = await CandidateRetrievalService(
        override_db_session, LocalEvidenceStorage(tmp_path)
    ).retrieve(case.id, source_candidate.id, FixtureDocumentProvider(document))

    artifact = override_db_session.get(RawArtifact, evidence.raw_artifact_id)
    assert artifact is not None
    assert artifact.content_hash == evidence.content_hash
    assert artifact.storage_key.startswith("raw/")
    assert evidence.provenance["candidate_id"] == source_candidate.id
    assert evidence.provenance["access_decided_by"] == "analyst@example.test"
    assert "possible business clue" in evidence.relevant_excerpt

    with pytest.raises(ValueError, match="does not match its raw artifact"):
        ResearchCaseService(override_db_session).add_evidence(
            case.id,
            source_mode="case_specific_research",
            canonical_url=document.url,
            publisher="Fictional Public Notices",
            source_type="probate_public_notice",
            content=b"different bytes",
            relevant_excerpt=None,
            extracted_facts={},
            provenance={},
            raw_artifact_id=artifact.id,
        )


@pytest.mark.asyncio
async def test_retrieval_requires_immutable_access_approval(override_db_session, tmp_path):
    case, source_candidate = await candidate(override_db_session)
    service = SearchService(override_db_session)
    service.decide_access(
        source_candidate.id,
        decision="blocked",
        reason="Publisher reuse terms are unclear.",
        decided_by="analyst@example.test",
    )

    with pytest.raises(ValueError, match="lacks an approved access decision"):
        await CandidateRetrievalService(
            override_db_session, LocalEvidenceStorage(tmp_path)
        ).retrieve(
            case.id,
            source_candidate.id,
            FixtureDocumentProvider(),
        )
    with pytest.raises(ValueError, match="immutable"):
        service.decide_access(
            source_candidate.id,
            decision="approved",
            reason="Changed mind.",
            decided_by="analyst@example.test",
        )
    assert override_db_session.scalar(
        select(func.count(CaseEvidence.id)).where(CaseEvidence.case_id == case.id)
    ) == 0


@pytest.mark.asyncio
async def test_blocking_access_observation_overrides_approval(override_db_session, tmp_path):
    case, source_candidate = await candidate(
        override_db_session, observations={"captcha": True}
    )
    SearchService(override_db_session).decide_access(
        source_candidate.id,
        decision="approved",
        reason="Page is public, subject to automated safety enforcement.",
        decided_by="analyst@example.test",
    )

    with pytest.raises(ValueError, match="blocking access observation"):
        await CandidateRetrievalService(
            override_db_session, LocalEvidenceStorage(tmp_path)
        ).retrieve(case.id, source_candidate.id, FixtureDocumentProvider())


@pytest.mark.asyncio
async def test_network_guard_rejects_local_and_private_addresses():
    for url in ("http://localhost/resource", "http://127.0.0.1/resource", "http://10.0.0.8/"):
        with pytest.raises(ValueError, match="non-public host"):
            await assert_public_network_url(url)
