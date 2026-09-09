"""Freeze only transition evidence that has already reproduced locally."""

from dataclasses import dataclass
from hashlib import sha256
from html import unescape
import re
from typing import Any
from urllib.parse import urlsplit

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import CaseEvidence, RawArtifact, ResearchCase, SourceCandidate
from app.research.cases import ResearchCaseService
from app.research.retrieval import CandidateRetrievalService, DocumentProvider
from app.research.search import SearchService, canonicalize_public_url
from app.storage.base import EvidenceStorage


@dataclass(frozen=True)
class FrozenEvidence:
    evidence_id: int
    raw_artifact_id: int
    canonical_url: str
    content_hash: str
    excerpt: str


async def preflight_case(
    db: Session,
    storage: EvidenceStorage,
    provider: DocumentProvider,
    case_spec: dict[str, Any],
    existing_case: ResearchCase | None = None,
) -> tuple[int, list[FrozenEvidence]]:
    """Retrieve every declared anchor before returning any frozen packet."""
    cases = ResearchCaseService(db)
    case = existing_case or cases.create_case(
        case_spec["origin"],
        {
            "max_queries": 0,
            "max_documents": len(case_spec["sources"]),
            "max_model_calls": 0,
            "max_steps": len(case_spec["sources"]),
            "max_elapsed_seconds": 1_200,
            "max_cost_cents": 0,
        },
    )
    retrieval = CandidateRetrievalService(db, storage)
    search = SearchService(db)
    frozen: list[FrozenEvidence] = []
    for source in case_spec["sources"]:
        canonical_url, domain = canonicalize_public_url(source["url"])
        evidence = db.scalar(
            select(CaseEvidence).where(
                CaseEvidence.case_id == case.id,
                CaseEvidence.canonical_url == canonical_url,
            )
        )
        if evidence is None:
            candidate = SourceCandidate(
                case_id=case.id,
                canonical_url=canonical_url,
                domain=domain,
                publisher=source["publisher"],
                likely_source_type=source["source_type"],
                geography={"state": case_spec["state"]},
                relevance_reason="Manually qualified Milestone 4.7 public anchor.",
                proposed_use="transition_packet_preflight",
                search_provider="manual_preflight",
                access_observations={"ordinary_public_page": True},
            )
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
            search.decide_access(
                candidate.id,
                decision="approved",
                reason="Ordinary public page reviewed for bounded retrieval without an access control.",
                decided_by="Milestone 4.7 preflight",
            )
            evidence = await retrieval.retrieve(case.id, candidate.id, provider)
        artifact = db.get(RawArtifact, evidence.raw_artifact_id)
        if artifact is None:
            raise RuntimeError("Preflight evidence lost its immutable artifact")
        content = storage.read(artifact.storage_key)
        if sha256(content).hexdigest() != artifact.content_hash:
            raise ValueError("Preflight artifact no longer matches its stored hash")
        page_text = visible_text(content.decode("utf-8", errors="replace"))
        excerpt = exact_excerpt(page_text, source["excerpt"])
        evidence.relevant_excerpt = excerpt
        evidence.extracted_facts = source.get("facts", {})
        db.commit()
        frozen.append(
            FrozenEvidence(
                evidence.id,
                artifact.id,
                evidence.canonical_url,
                artifact.content_hash,
                excerpt,
            )
        )
    return case.id, frozen


def validate_candidate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != "milestone-4-7-preflight-candidates-v1":
        raise ValueError("Unexpected preflight manifest schema")
    cases = manifest.get("cases")
    expected = [("CO", "signal_first"), ("UT", "business_first"), ("TX", "hybrid")]
    if not isinstance(cases, list) or [
        (case.get("state"), case.get("origin")) for case in cases
    ] != expected:
        raise ValueError("Preflight requires the fixed state and origin sequence")
    for case in cases:
        sources = case.get("sources")
        if not isinstance(sources, list) or len(sources) < 2:
            raise ValueError("Each preflight case requires at least two sources")
        for source in sources:
            if urlsplit(source.get("url", "")).scheme != "https":
                raise ValueError("Preflight sources require HTTPS")
            if not all(source.get(field) for field in ("publisher", "source_type", "excerpt")):
                raise ValueError("Preflight source metadata is incomplete")


def visible_text(html: str) -> str:
    without_scripts = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", without_scripts)).split())


def exact_excerpt(page_text: str, expected: str) -> str:
    normalized = " ".join(expected.split())
    if normalized.casefold() not in page_text.casefold():
        raise ValueError("Qualified excerpt is absent from the retrieved artifact")
    return normalized
