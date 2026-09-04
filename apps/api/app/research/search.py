from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.models import (
    ResearchCase,
    ResearchQuery,
    Source,
    SourceCandidate,
    SourceCandidateDiscovery,
)
from app.research.ingestion import assert_safe_source_content


SOURCE_TYPES = frozenset(
    {
        "obituary",
        "funeral_home",
        "newspaper",
        "business_website",
        "government",
        "licensing",
        "professional_association",
        "business_directory",
        "probate_public_notice",
        "other",
    }
)


@dataclass(frozen=True)
class SearchResult:
    url: str
    title: str
    relevance_reason: str
    proposed_use: str
    publisher: str | None = None
    likely_source_type: str = "other"
    geography: dict[str, str] = field(default_factory=dict)
    access_observations: dict[str, bool] = field(default_factory=dict)


class SearchProvider(ABC):
    key: str

    @abstractmethod
    async def search(self, query: str, max_results: int) -> list[SearchResult]: ...


class FixtureSearchProvider(SearchProvider):
    """Deterministic provider for contract tests; it never performs network access."""

    key = "fixture"

    def __init__(self, results: list[SearchResult] | None = None, error: Exception | None = None):
        self.results = results or []
        self.error = error

    async def search(self, query: str, max_results: int) -> list[SearchResult]:
        if self.error is not None:
            raise self.error
        return self.results[:max_results]


class SearchService:
    """Execute bounded search and stage results as candidates, never as evidence."""

    def __init__(self, db: Session):
        self.db = db

    async def execute(
        self,
        case_id: int,
        provider: SearchProvider,
        query_text: str,
        *,
        max_results: int = 10,
    ) -> list[SourceCandidate]:
        case = self.db.get(ResearchCase, case_id)
        if case is None:
            raise ValueError("Research case does not exist")
        if not query_text.strip() or len(query_text) > 500:
            raise ValueError("Search query must contain between 1 and 500 characters")
        if not provider.key.strip():
            raise ValueError("Search provider requires a stable key")
        if not 1 <= max_results <= 20:
            raise ValueError("Search result limit must be between 1 and 20")
        used_queries = self.db.scalar(
            select(func.count(ResearchQuery.id)).where(ResearchQuery.case_id == case_id)
        ) or 0
        if used_queries >= int(case.research_budget.get("max_queries", 0)):
            raise ValueError("Research case query budget is exhausted")

        query = ResearchQuery(
            case_id=case_id,
            query_text=query_text.strip(),
            provider=provider.key,
            max_results=max_results,
        )
        self.db.add(query)
        self.db.commit()
        self.db.refresh(query)
        started = perf_counter()
        try:
            results = await provider.search(query.query_text, max_results)
            if len(results) > max_results:
                raise ValueError("Search provider exceeded the requested result limit")
            candidates = [
                self._stage_candidate(case, query, result, rank)
                for rank, result in enumerate(results, start=1)
            ]
        except Exception as error:
            # Keep one provider call atomic: malformed later results must not
            # leave earlier candidates looking like a successful partial set.
            self.db.rollback()
            query = self.db.get(ResearchQuery, query.id)
            if query is None:
                raise RuntimeError("Search query audit record was lost") from error
            query.status = "failed"
            query.finished_at = datetime.now(timezone.utc)
            query.latency_ms = round((perf_counter() - started) * 1000)
            query.error_class = type(error).__name__
            self.db.commit()
            raise
        query.status = "succeeded"
        query.finished_at = datetime.now(timezone.utc)
        query.latency_ms = round((perf_counter() - started) * 1000)
        query.result_count = len(results)
        self.db.commit()
        return candidates

    def promote(
        self, candidate_id: int, known_source_id: int, *, decision_reason: str
    ) -> SourceCandidate:
        candidate = self.db.get(SourceCandidate, candidate_id)
        known_source = self.db.get(Source, known_source_id)
        if candidate is None or known_source is None:
            raise ValueError("Candidate and evaluated known source must both exist")
        if not decision_reason.strip():
            raise ValueError("Source promotion requires an evaluation reason")
        candidate.status = "promoted"
        candidate.promoted_source_id = known_source_id
        candidate.promotion_reason = decision_reason.strip()
        candidate.promoted_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def _stage_candidate(
        self,
        case: ResearchCase,
        query: ResearchQuery,
        result: SearchResult,
        rank: int,
    ) -> SourceCandidate:
        canonical_url, domain = canonicalize_public_url(result.url)
        if not result.relevance_reason.strip() or not result.proposed_use.strip():
            raise ValueError("Search results require relevance reason and proposed use")
        assert_safe_source_content(result.geography)
        assert_safe_source_content(result.access_observations)
        source_type = (
            result.likely_source_type
            if result.likely_source_type in SOURCE_TYPES
            else "other"
        )
        candidate = self.db.scalar(
            select(SourceCandidate).where(
                SourceCandidate.case_id == case.id,
                SourceCandidate.canonical_url == canonical_url,
            )
        )
        if candidate is None:
            candidate = SourceCandidate(
                case_id=case.id,
                canonical_url=canonical_url,
                domain=domain,
                publisher=result.publisher,
                likely_source_type=source_type,
                geography=result.geography,
                relevance_reason=result.relevance_reason,
                proposed_use=result.proposed_use,
                search_provider=query.provider,
                access_observations=result.access_observations,
            )
            self.db.add(candidate)
            self.db.flush()
        existing_discovery = self.db.scalar(
            select(SourceCandidateDiscovery).where(
                SourceCandidateDiscovery.candidate_id == candidate.id,
                SourceCandidateDiscovery.query_id == query.id,
            )
        )
        if existing_discovery is None:
            self.db.add(
                SourceCandidateDiscovery(
                    candidate_id=candidate.id, query_id=query.id, result_rank=rank
                )
            )
            self.db.flush()
        return candidate


def canonicalize_public_url(url: str) -> tuple[str, str]:
    parts = urlsplit(url.strip())
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("Search results require a public HTTP(S) URL")
    hostname = parts.hostname.lower()
    netloc = hostname
    if parts.port and not (
        (parts.scheme == "http" and parts.port == 80)
        or (parts.scheme == "https" and parts.port == 443)
    ):
        netloc = f"{hostname}:{parts.port}"
    canonical = urlunsplit((parts.scheme.lower(), netloc, parts.path or "/", parts.query, ""))
    return canonical, hostname
