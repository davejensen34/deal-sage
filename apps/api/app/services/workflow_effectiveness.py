from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.domain.models import (
    AcquisitionRun, CandidateMatch, CaseEvidence, CuratedRecord, RawArtifact,
    ResearchCase, ReviewCase, RunArtifact, SourceRefresh,
)


def workflow_effectiveness(db: Session) -> dict[str, Any]:
    """Measure durable source-to-review lineage without probabilistic attribution."""
    candidates = db.scalars(select(CandidateMatch).order_by(CandidateMatch.id)).all()
    reviews = {row.candidate_id: row for row in db.scalars(select(ReviewCase)).all()}
    candidate_sources, lineage_available = _candidate_source_keys(db)
    source_keys = set(db.scalars(select(AcquisitionRun.source_key)).all())
    source_keys.update(db.scalars(select(SourceRefresh.source_key)).all())
    source_keys.update(key for keys in candidate_sources.values() for key in keys)

    sources = []
    for source_key in sorted(source_keys):
        runs = db.scalars(select(AcquisitionRun).where(AcquisitionRun.source_key == source_key)).all()
        refreshes = db.scalars(select(SourceRefresh).where(SourceRefresh.source_key == source_key)).all()
        artifact_ids = set(db.scalars(
            select(RunArtifact.artifact_id)
            .join(AcquisitionRun, AcquisitionRun.id == RunArtifact.run_id)
            .where(AcquisitionRun.source_key == source_key)
        ).all())
        curated = db.scalars(select(CuratedRecord).where(CuratedRecord.artifact_id.in_(artifact_ids))).all() if artifact_ids else []
        attributed_ids = sorted(candidate_id for candidate_id, keys in candidate_sources.items() if source_key in keys)
        decisions = Counter()
        reasons = Counter()
        for candidate_id in attributed_ids:
            review = reviews.get(candidate_id)
            if review and review.decision:
                decisions[review.decision] += 1
            if review:
                reasons.update(review.decision_reason_codes or [])
        freshness = Counter(row.freshness_status for row in refreshes)
        sources.append({
            "source_key": source_key,
            "jurisdictions": sorted({row.jurisdiction for row in runs} | {row.jurisdiction for row in refreshes}),
            "acquisition_runs": len(runs),
            "refresh_runs": len(refreshes),
            "refresh_outcomes": dict(sorted(Counter(row.status for row in refreshes).items())),
            "unique_artifacts": len(artifact_ids),
            "curated_records": sum(row.status == "curated" for row in curated),
            "quarantined_records": sum(row.status == "quarantined" for row in curated),
            "recorded_refresh_cost_usd": round(sum(row.actual_cost_usd for row in refreshes), 4),
            "freshness_outcomes": dict(sorted(freshness.items())),
            "latest_refresh_at": max((value for row in refreshes if (value := row.finished_at or row.started_at) is not None), default=None),
            "attributed_candidates": len(attributed_ids),
            "analyst_decisions": dict(sorted(decisions.items())),
            "decision_reason_codes": dict(sorted(reasons.items())),
        })

    attributed_ids = set(candidate_sources)
    all_decisions = Counter(review.decision for review in reviews.values() if review.decision)
    return {
        "candidate_total": len(candidates),
        "attributed_candidates": len(attributed_ids),
        "unattributed_candidates": len(candidates) - len(attributed_ids),
        "attribution_coverage_percent": round(len(attributed_ids) / len(candidates) * 100, 1) if candidates else 0,
        "analyst_decisions": dict(sorted(all_decisions.items())),
        "sources": sources,
        "measurement_boundaries": {
            "attribution_basis": "research_case_evidence_to_raw_artifact_to_acquisition_run",
            "durable_lineage_available": lineage_available,
            "lineage_unavailable_reason": None if lineage_available else "case_evidence_raw_artifact_link_not_migrated",
            "multi_source_candidate_counts_are_additive": False,
            "unlinked_candidates_are_not_inferred": True,
            "cost_scope": "source_refresh_records_only",
            "raw_record_content_included": False,
        },
    }


def _candidate_source_keys(db: Session) -> tuple[dict[int, set[str]], bool]:
    # Long-lived single-box databases may predate this additive lineage column.
    # Reporting must remain available and must not replace the absent link with
    # a name, state, publisher, or timing guess.
    columns = {column["name"] for column in inspect(db.get_bind()).get_columns("case_evidence")}
    if "raw_artifact_id" not in columns:
        return {}, False
    rows = db.execute(
        select(ResearchCase.candidate_match_id, RawArtifact.source_key)
        .join(CaseEvidence, CaseEvidence.case_id == ResearchCase.id)
        .join(RawArtifact, RawArtifact.id == CaseEvidence.raw_artifact_id)
        .where(ResearchCase.candidate_match_id.is_not(None))
        .distinct()
    ).all()
    result: dict[int, set[str]] = defaultdict(set)
    for candidate_id, source_key in rows:
        result[candidate_id].add(source_key)
    return dict(result), True
