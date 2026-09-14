"""Freeze recent-signal evaluation requests without credentials or external calls."""

from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.domain.models import CaseEvidence, ClaimContradiction, EvidenceClaim, RawArtifact, ResearchCase, SourceCandidate
from app.research.analysis_preparation import MODEL, canonical_bytes
from app.research.ingestion import assert_safe_source_content
from app.research.observation_contract import INSTRUCTIONS, OBSERVATION_SCHEMA, VERSION
from app.research.signal_freshness import assess_intake, validate_policy
from app.research.search import canonicalize_public_url
from app.research.transitions import signal_type_for

PREPARATION = "m7-analysis-preparation-v3"
EXECUTION = "m7-analysis-execution-v4"


class StrictRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class EvidenceSnapshot(StrictRecord):
    id: int = Field(gt=0)
    artifact_id: int = Field(gt=0)
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    canonical_url: str = Field(max_length=1000)
    publisher: str = Field(max_length=200)
    source_type: str = Field(max_length=60)
    published_at: str | None
    retrieved_at: str
    relevant_excerpt: str = Field(min_length=1, max_length=12000)
    candidate_id: int = Field(gt=0)
    access_decision: Literal["approved"]
    access_decided_by: str = Field(min_length=1, max_length=160)


class ClaimSnapshot(StrictRecord):
    id: int = Field(gt=0)
    evidence_id: int = Field(gt=0)
    subject_type: str = Field(max_length=50)
    object_value: dict
    status: str = Field(max_length=30)
    classification: str = Field(max_length=40)
    source_authority: str = Field(max_length=30)
    directness: str = Field(max_length=30)


class CaseSnapshot(StrictRecord):
    case_id: int = Field(gt=0)
    requested_state: Literal["CO", "UT", "TX"]
    origin: Literal["signal_first", "business_first", "hybrid"]
    policy: dict
    evidence: list[EvidenceSnapshot] = Field(max_length=30)
    claims: list[ClaimSnapshot] = Field(max_length=100)
    conflicted_claim_ids: list[int] = Field(max_length=200)


class IntakeSnapshot(StrictRecord):
    version: Literal["m7-signal-intake-v1"]
    cases: list[CaseSnapshot] = Field(min_length=1, max_length=20)


def strict_json(payload: bytes) -> dict:
    if len(payload) > 2_000_000:
        raise ValueError("Frozen intake exceeds file byte limit")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate frozen intake key")
            result[key] = value
        return result

    def invalid_constant(_):
        raise ValueError("Non-finite frozen intake number")

    return json.loads(payload, object_pairs_hook=pairs, parse_constant=invalid_constant)


def _unique(values):
    if len(set(values)) != len(values):
        raise ValueError("Duplicate frozen intake identifier")


def prepare_snapshot(snapshot: dict) -> dict:
    """Recompute routes and requests, never trust serialized eligibility flags.

    Date assertions are attributed claim records; their source excerpts are
    checked by the shared intake policy. They are not human ground truth.
    """
    intake = IntakeSnapshot.model_validate(snapshot)
    _unique([case.case_id for case in intake.cases])
    _unique([e.id for case in intake.cases for e in case.evidence])
    _unique([c.id for case in intake.cases for c in case.claims])
    reports, requests = [], []
    policies = []
    for case in intake.cases:
        policy = validate_policy(case.policy)
        policies.append(policy)
        evidence = {}
        for source in case.evidence:
            canonicalize_public_url(source.canonical_url)
            evidence[source.id] = CaseEvidence(
                id=source.id, case_id=case.case_id, relevant_excerpt=source.relevant_excerpt,
                published_at=datetime.fromisoformat(source.published_at) if source.published_at else None,
                retrieved_at=datetime.fromisoformat(source.retrieved_at),
            )
        claims = [EvidenceClaim(**claim.model_dump(), case_id=case.case_id, predicate="transition") for claim in case.claims]
        if any(claim.evidence_id not in evidence for claim in claims):
            raise ValueError("Frozen claim lacks same-case evidence")
        report = assess_intake([(c, evidence[c.evidence_id]) for c in claims], policy,
                               conflicted_ids=case.conflicted_claim_ids)
        slot = f"M7-RECENT-{case.case_id}"
        reports.append({"slot": slot, "case_id": case.case_id, **report})
        if not report["analysis_allowed"]:
            continue
        eligible_ids = {row["claim_id"] for row in report["signals"] if row["eligible"]}
        signal_types = {signal_type_for(c) for c in claims if c.id in eligible_ids}
        if len(signal_types) != 1:
            raise ValueError("Evaluation case requires one eligible signal family")
        # Only retained source excerpts reach the model; normalized assertions,
        # routing decisions and expected analyst judgments remain outside input.
        context = {"case_origin": case.origin, "requested_state": case.requested_state,
                   "signal_type": next(iter(signal_types)), "as_of": policy["assessment_date"],
                   "sources": [{"source_id": str(s.id), "url": s.canonical_url,
                                "text": s.relevant_excerpt} for s in case.evidence]}
        request = {"model": MODEL, "instructions": INSTRUCTIONS, "input": canonical_bytes(context).decode(),
                   "max_output_tokens": 6000, "store": False, "tools": [], "truncation": "disabled",
                   "text": {"format": {"type": "json_schema", "name": "m7_observation_v2", "strict": True,
                                         "schema": deepcopy(OBSERVATION_SCHEMA)}}}
        if len(canonical_bytes(request)) > 16000:
            raise ValueError("Frozen request exceeds byte ceiling; curate a smaller case")
        assert_safe_source_content(context)
        requests.append({"slot": slot, "request": request, "request_sha256": sha256(canonical_bytes(request)).hexdigest()})
    if any(policy != policies[0] for policy in policies):
        raise ValueError("A cohort must share one frozen assessment policy")
    if len(requests) > 3:
        raise ValueError("More than three eligible cases; curate the cohort explicitly")
    bundle = {"protocol": PREPARATION, "execution_protocol": EXECUTION, "observation_contract": VERSION,
            "approval_status": "not_authorized", "intake_snapshot": snapshot,
            "intake_sha256": sha256(canonical_bytes(snapshot)).hexdigest(), "intake_reports": reports,
            "cohort_counts": {"considered": len(reports), "eligible": len(requests),
                              "excluded": len(reports) - len(requests)},
            "requests": requests, "limits": {"calls": len(requests), "max_retries": 0,
                "max_input_tokens_per_call": 20000, "max_output_tokens_per_call": 6000,
                "reserved_cents_per_call": 5, "reserved_cents_total": len(requests) * 5,
                "searches": 0, "promotions": 0}}
    if len(canonical_bytes(bundle)) > 2_000_000:
        raise ValueError("Frozen intake exceeds file byte limit")
    return bundle


def validate_bundle(payload: bytes) -> dict:
    bundle = strict_json(payload)
    regenerated = prepare_snapshot(bundle["intake_snapshot"])
    if canonical_bytes(regenerated) != canonical_bytes(bundle):
        raise ValueError("Frozen requests or intake routing do not reproduce")
    if not regenerated["requests"]:
        raise ValueError("No eligible recent packets; no analysis slots may be reserved")
    return regenerated


def freeze_cases(db, selections: list[tuple[int, str]], read_artifact) -> dict:
    """Snapshot complete selected cases; verify retained raw bytes before freezing.

    The caller supplies a read-only transaction and a contained evidence reader.
    No claims are created, dates invented, or source access decisions granted.
    """
    if not 1 <= len(selections) <= 20:
        raise ValueError("Select between one and twenty cases")
    _unique([case_id for case_id, _ in selections])
    cases = []
    for case_id, state in selections:
        case = db.get(ResearchCase, case_id)
        if case is None or case.signal_intake_policy is None:
            raise ValueError("Selected case requires an explicit signal intake policy")
        claims = db.scalars(select(EvidenceClaim).where(
            EvidenceClaim.case_id == case_id, EvidenceClaim.predicate == "transition"
        ).order_by(EvidenceClaim.id)).all()
        sources = db.scalars(select(CaseEvidence).where(CaseEvidence.case_id == case_id).order_by(CaseEvidence.id)).all()
        evidence = []
        for source in sources:
            candidate_id = source.provenance.get("candidate_id")
            candidate = db.get(SourceCandidate, candidate_id) if type(candidate_id) is int else None
            if candidate is None or candidate.case_id != case_id or candidate.access_decision != "approved":
                raise ValueError("Frozen evaluation requires an approved same-case source candidate")
            artifact = db.get(RawArtifact, source.raw_artifact_id) if source.raw_artifact_id else None
            if artifact is None or artifact.content_hash != source.content_hash or artifact.canonical_url != source.canonical_url:
                raise ValueError("Frozen evidence requires matching retained artifact lineage")
            raw = read_artifact(artifact.storage_key)
            if len(raw) != artifact.byte_size or sha256(raw).hexdigest() != source.content_hash:
                raise ValueError("Frozen evidence bytes do not match retained lineage")
            evidence.append({"id": source.id, "artifact_id": artifact.id, "content_hash": source.content_hash,
                "canonical_url": source.canonical_url, "publisher": source.publisher, "source_type": source.source_type,
                "candidate_id": candidate.id, "access_decision": candidate.access_decision,
                "access_decided_by": candidate.access_decided_by,
                "published_at": source.published_at.isoformat() if source.published_at else None,
                "retrieved_at": source.retrieved_at.isoformat(), "relevant_excerpt": source.relevant_excerpt})
        conflicts = db.scalars(select(ClaimContradiction).where(
            ClaimContradiction.case_id == case_id, ClaimContradiction.status == "open"
        )).all()
        cases.append({"case_id": case_id, "requested_state": state, "origin": case.origin_strategy,
            "policy": case.signal_intake_policy, "evidence": evidence,
            "claims": [{key: getattr(c, key) for key in ClaimSnapshot.model_fields} for c in claims],
            "conflicted_claim_ids": sorted({cid for c in conflicts for cid in (c.left_claim_id, c.right_claim_id)})})
    return prepare_snapshot({"version": "m7-signal-intake-v1", "cases": cases})
