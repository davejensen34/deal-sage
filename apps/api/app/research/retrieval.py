"""Permissioned, bounded retrieval for dynamically discovered public sources."""

from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.models import CaseEvidence, ResearchCase, SourceCandidate
from app.research.cases import ResearchCaseService
from app.research.landing import EvidenceLanding, LandingEnvelope
from app.research.search import canonicalize_public_url
from app.storage.base import EvidenceStorage


MAX_RETRIEVAL_BYTES = 1_000_000
SUPPORTED_MEDIA_TYPES = frozenset({"text/html", "text/plain", "application/json"})
BLOCKING_ACCESS_FLAGS = frozenset(
    {"authentication_required", "paywall", "captcha", "robots_disallowed", "reuse_prohibited"}
)


@dataclass(frozen=True)
class RetrievedDocument:
    url: str
    content: bytes
    media_type: str
    retrieved_at: datetime


class DocumentProvider(ABC):
    key: str

    @abstractmethod
    async def retrieve(self, url: str, *, max_bytes: int) -> RetrievedDocument: ...


class FixtureDocumentProvider(DocumentProvider):
    """Offline provider used to test the same retrieval contract as live HTTP."""

    key = "fixture"

    def __init__(self, document: RetrievedDocument | None = None, error: Exception | None = None):
        self.document = document
        self.error = error

    async def retrieve(self, url: str, *, max_bytes: int) -> RetrievedDocument:
        if self.error is not None:
            raise self.error
        if self.document is None:
            raise ValueError("Fixture document is not configured")
        if len(self.document.content) > max_bytes:
            raise ValueError("Retrieved document exceeds the byte limit")
        return self.document


class HttpDocumentProvider(DocumentProvider):
    """Retrieve ordinary public documents with redirect and SSRF defenses."""

    key = "public_http"

    def __init__(self, *, timeout_seconds: float = 15, max_redirects: int = 3):
        self.timeout_seconds = timeout_seconds
        self.max_redirects = max_redirects

    async def retrieve(self, url: str, *, max_bytes: int) -> RetrievedDocument:
        current = url
        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            follow_redirects=False,
            headers={"User-Agent": "DealSage/0.1 responsible-research"},
        ) as client:
            for redirect_count in range(self.max_redirects + 1):
                await assert_public_network_url(current)
                async with client.stream("GET", current) as response:
                    if response.is_redirect:
                        if redirect_count == self.max_redirects or not response.headers.get("location"):
                            raise ValueError("Retrieval redirect limit exceeded")
                        current = urljoin(current, response.headers["location"])
                        continue
                    response.raise_for_status()
                    media_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
                    if media_type not in SUPPORTED_MEDIA_TYPES:
                        raise ValueError("Retrieved document media type is not supported")
                    content = bytearray()
                    async for chunk in response.aiter_bytes():
                        content.extend(chunk)
                        if len(content) > max_bytes:
                            raise ValueError("Retrieved document exceeds the byte limit")
                    return RetrievedDocument(
                        url=str(response.url),
                        content=bytes(content),
                        media_type=media_type,
                        retrieved_at=datetime.now(timezone.utc),
                    )
        raise RuntimeError("Retrieval ended without a response")


class CandidateRetrievalService:
    """Land approved candidate bytes before creating minimal case evidence."""

    def __init__(self, db: Session, storage: EvidenceStorage):
        self.db = db
        self.landing = EvidenceLanding(db, storage)
        self.cases = ResearchCaseService(db)

    async def retrieve(
        self,
        case_id: int,
        candidate_id: int,
        provider: DocumentProvider,
        *,
        max_bytes: int = MAX_RETRIEVAL_BYTES,
    ) -> CaseEvidence:
        case = self.db.get(ResearchCase, case_id)
        candidate = self.db.get(SourceCandidate, candidate_id)
        if case is None or candidate is None or candidate.case_id != case.id:
            raise ValueError("Retrieval requires a same-case source candidate")
        if candidate.access_decision != "approved":
            raise ValueError("Source candidate lacks an approved access decision")
        if any(candidate.access_observations.get(flag) is True for flag in BLOCKING_ACCESS_FLAGS):
            raise ValueError("Source candidate has a blocking access observation")
        if not 1 <= max_bytes <= MAX_RETRIEVAL_BYTES:
            raise ValueError("Retrieval byte limit is outside its bounds")
        document_count = self.db.scalar(
            select(func.count(CaseEvidence.id)).where(CaseEvidence.case_id == case.id)
        ) or 0
        if document_count >= int(case.research_budget.get("max_documents", 0)):
            raise ValueError("Research case document budget is exhausted")

        canonical_url, _ = canonicalize_public_url(candidate.canonical_url)
        assert_nonlocal_url(canonical_url)
        document = await provider.retrieve(canonical_url, max_bytes=max_bytes)
        final_url, _ = canonicalize_public_url(document.url)
        assert_nonlocal_url(final_url)
        if len(document.content) == 0 or len(document.content) > max_bytes:
            raise ValueError("Retrieved document content is empty or over budget")
        if document.media_type.lower() not in SUPPORTED_MEDIA_TYPES:
            raise ValueError("Retrieved document media type is not supported")

        fingerprint = sha256(
            f"{provider.key}|{candidate.domain}|permissioned-retrieval-v1".encode()
        ).hexdigest()
        run = self.landing.start_run(
            f"dynamic:{candidate.domain}",
            candidate.geography.get("state", "case-specific"),
            case.origin_strategy,
            fingerprint,
        )
        artifact = self.landing.land_artifact(
            run,
            LandingEnvelope(
                source_key=run.source_key,
                source_record_id=str(candidate.id),
                canonical_url=final_url,
                retrieved_at=document.retrieved_at,
                media_type=document.media_type.lower(),
                contract_fingerprint=fingerprint,
                request_metadata={
                    "candidate_id": candidate.id,
                    "provider": provider.key,
                    "access_decision": candidate.access_decision,
                },
                content=document.content,
            ),
        )
        self.landing.finish_artifact_run(run)
        existing = self.db.scalar(
            select(CaseEvidence).where(
                CaseEvidence.case_id == case.id,
                CaseEvidence.raw_artifact_id == artifact.id,
            )
        )
        if existing is not None:
            # Re-observing identical bytes is useful acquisition provenance, but
            # it is not new evidence and must not inflate case confidence.
            return existing
        excerpt = _bounded_text_excerpt(document.content, document.media_type)
        return self.cases.add_evidence(
            case.id,
            source_mode="case_specific_research",
            canonical_url=final_url,
            publisher=candidate.publisher or candidate.domain,
            source_type=candidate.likely_source_type,
            content=document.content,
            relevant_excerpt=excerpt,
            extracted_facts={},
            provenance={
                "candidate_id": candidate.id,
                "raw_artifact_id": artifact.id,
                "retrieval_provider": provider.key,
                "access_decided_by": candidate.access_decided_by,
            },
            raw_artifact_id=artifact.id,
        )


async def assert_public_network_url(url: str) -> None:
    """Reject local/special address space for every requested or redirected URL."""
    hostname = assert_nonlocal_url(url)
    try:
        literal = ipaddress.ip_address(hostname)
        addresses = [literal]
    except ValueError:
        loop = asyncio.get_running_loop()
        infos = await loop.run_in_executor(None, socket.getaddrinfo, hostname, None)
        addresses = list({ipaddress.ip_address(info[4][0]) for info in infos})
    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("Retrieval URL resolves to a non-public host")


def assert_nonlocal_url(url: str) -> str:
    """Reject obvious local hosts before any provider, including offline fixtures."""
    _, hostname = canonicalize_public_url(url)
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("Retrieval URL resolves to a non-public host")
    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        return hostname
    if not literal.is_global:
        raise ValueError("Retrieval URL resolves to a non-public host")
    return hostname


def _bounded_text_excerpt(content: bytes, media_type: str) -> str | None:
    if media_type not in {"text/html", "text/plain", "application/json"}:
        return None
    return content.decode("utf-8", errors="replace")[:2_000]
