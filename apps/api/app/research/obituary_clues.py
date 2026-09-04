from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import re
from typing import Any

from sqlalchemy.orm import Session

from app.domain.models import CaseEvidence, EvidenceClaim
from app.research.cases import RELATIONSHIP_SEMANTICS, ResearchCaseService
from app.research.ingestion import assert_safe_source_content


OBITUARY_SOURCE_TYPES = frozenset({"obituary", "funeral_home", "newspaper"})


@dataclass(frozen=True)
class BusinessClue:
    """A source-stated business relationship, not a DealSage ownership conclusion."""

    business_name: str
    relationship_semantics: str
    relevant_excerpt: str
    confidence: float
    trade_or_industry: str | None = None
    geography: dict[str, str] = field(default_factory=dict)
    dates: dict[str, str] = field(default_factory=dict)
    succession_references: tuple[str, ...] = ()


class BusinessClueExtractor(ABC):
    """Provider-neutral boundary for deterministic or model-backed extraction."""

    key: str
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None

    @abstractmethod
    async def extract(self, text: str) -> list[BusinessClue]: ...


class DeterministicBusinessClueExtractor(BusinessClueExtractor):
    """Extract only explicit relationship phrases with conservative boundaries.

    This intentionally prefers missed clues to inferred ownership. It provides a
    reproducible baseline and test oracle for later model-backed extraction.
    """

    key = "deterministic-relationship-phrases-v1"

    _patterns = (
        ("former_owner", re.compile(r"\b(?:former|previous) (?:co-)?owner of (?P<business>[^,.;]+)", re.I)),
        ("co_owner", re.compile(r"\bco-(?:owned|owner of) (?P<business>[^,.;]+)", re.I)),
        (
            "owner",
            re.compile(
                r"(?<!former )(?<!previous )(?<!co-)\b(?:owned|owner of) (?P<business>[^,.;]+)",
                re.I,
            ),
        ),
        ("founder", re.compile(r"\b(?:founded|founder of) (?P<business>[^,.;]+)", re.I)),
        ("operator", re.compile(r"\b(?:operated|operator of) (?P<business>[^,.;]+)", re.I)),
        (
            "family_business_participant",
            re.compile(r"\b(?:worked (?:in|at)|helped run) (?:the )?family business[, ]+(?P<business>[^,.;]+)", re.I),
        ),
        (
            "executive",
            re.compile(r"\b(?:president|chief executive officer|CEO|executive) (?:of|at) (?P<business>[^,.;]+)", re.I),
        ),
        ("employee", re.compile(r"\b(?:worked (?:for|at)|was employed (?:by|at)) (?P<business>[^,.;]+)", re.I)),
        ("sold_business", re.compile(r"\bsold (?P<business>[^,.;]+?)(?:\s+in\s+\d{4})?(?=$|[,.;])", re.I)),
        ("retired", re.compile(r"\bretired from (?P<business>[^,.;]+?)(?:\s+in\s+\d{4})?(?=$|[,.;])", re.I)),
    )
    _trailing_context = re.compile(
        r"\s+(?:in|after|before|where|when|which|and)\s+.*$", re.I
    )
    _year = re.compile(r"\b(?:18|19|20)\d{2}\b")
    _succession = re.compile(
        r"\b(?:succeeded by|passed (?:the business|it) to|son|daughter|children|family continued)\b[^.;]*",
        re.I,
    )

    async def extract(self, text: str) -> list[BusinessClue]:
        clues: list[BusinessClue] = []
        seen: set[tuple[str, str, str]] = set()
        for excerpt in _sentences(text):
            for semantics, pattern in self._patterns:
                for match in pattern.finditer(excerpt):
                    business_name = self._clean_business_name(match.group("business"))
                    if not business_name:
                        continue
                    identity = (semantics, business_name.casefold(), excerpt)
                    if identity in seen:
                        continue
                    seen.add(identity)
                    years = self._year.findall(excerpt)
                    succession = tuple(
                        item.group(0).strip() for item in self._succession.finditer(excerpt)
                    )
                    clues.append(
                        BusinessClue(
                            business_name=business_name,
                            relationship_semantics=semantics,
                            relevant_excerpt=excerpt,
                            confidence=1.0,
                            dates={"mentioned_year": years[0]} if years else {},
                            succession_references=succession,
                        )
                    )
        return clues

    def _clean_business_name(self, value: str) -> str:
        value = self._trailing_context.sub("", value).strip(" \"'()")
        # Pronouns and generic nouns are context for research, not resolvable names.
        if value.casefold() in {"it", "the business", "his business", "her business"}:
            return ""
        return value[:200].strip()


class ObituaryClueService:
    """Persist validated extractor output as claims tied to obituary evidence."""

    def __init__(self, db: Session):
        self.db = db
        self.case_service = ResearchCaseService(db)

    async def extract_claims(
        self,
        case_id: int,
        evidence_id: int,
        extractor: BusinessClueExtractor,
        *,
        source_authority: str,
    ) -> list[EvidenceClaim]:
        evidence = self.db.get(CaseEvidence, evidence_id)
        if evidence is None or evidence.case_id != case_id:
            raise ValueError("Clue evidence must belong to the same research case")
        if evidence.source_type not in OBITUARY_SOURCE_TYPES:
            raise ValueError("Business-clue extraction requires obituary-like evidence")
        if not source_authority.strip() or not extractor.key.strip():
            raise ValueError("Extraction requires source authority and extractor identity")
        model_provenance = (extractor.provider, extractor.model, extractor.prompt_version)
        if any(model_provenance) and not all(model_provenance):
            raise ValueError(
                "Model-backed extraction requires provider, model, and prompt version"
            )

        clues = await extractor.extract(evidence.relevant_excerpt or "")
        # Validate the complete provider response before the first commit so a
        # malformed later clue cannot leave a misleading partial extraction.
        for clue in clues:
            self._validate_clue(clue, evidence)
        claims: list[EvidenceClaim] = []
        for clue in clues:
            claims.append(
                self.case_service.add_claim(
                    case_id,
                    evidence_id,
                    subject_type="person_business_relationship",
                    predicate="relationship",
                    object_value={
                        "business_name": clue.business_name,
                        "trade_or_industry": clue.trade_or_industry,
                        "geography": clue.geography,
                        "dates": clue.dates,
                        "succession_references": list(clue.succession_references),
                        "supporting_excerpt": clue.relevant_excerpt,
                        "extractor": {
                            "key": extractor.key,
                            "provider": extractor.provider,
                            "model": extractor.model,
                            "prompt_version": extractor.prompt_version,
                        },
                    },
                    relationship_semantics=clue.relationship_semantics,
                    confidence=clue.confidence,
                    classification="source_fact",
                    source_authority=source_authority.strip(),
                    directness="direct_statement",
                )
            )
        return claims

    @staticmethod
    def _validate_clue(clue: BusinessClue, evidence: CaseEvidence) -> None:
        if clue.relationship_semantics not in RELATIONSHIP_SEMANTICS - {"unknown", "registered_agent"}:
            raise ValueError("Extractor returned unsupported relationship semantics")
        if not clue.business_name.strip() or len(clue.business_name) > 200:
            raise ValueError("Extractor returned an invalid business name")
        if not 0 <= clue.confidence <= 1:
            raise ValueError("Extractor confidence must be between 0 and 1")
        if not clue.relevant_excerpt or clue.relevant_excerpt not in (evidence.relevant_excerpt or ""):
            raise ValueError("Every business clue must quote its supporting evidence excerpt")
        safe_output: dict[str, Any] = {
            "geography": clue.geography,
            "dates": clue.dates,
            "succession_references": list(clue.succession_references),
        }
        assert_safe_source_content(safe_output)


def _sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+|[\r\n]+", text) if sentence.strip()]
