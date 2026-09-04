from dataclasses import dataclass

WEIGHTS = {
    "owner_filing": 25, "exact_full_name": 15, "same_city": 12,
    "company_in_signal": 10, "independent_source": 10, "age_aligns": 8,
    "timeline_aligns": 7, "occupation_aligns": 6, "relative_overlap": 7,
    "address_overlap": 12, "registered_agent_only": -35, "geography_conflict": -24,
    "former_owner": -30, "age_contradiction": -28, "common_name": -15,
    "insufficient_diversity": -12, "stale_source": -8,
}


@dataclass
class ScoreResult:
    score: int
    contributions: list[dict]


def score_features(features: list[str]) -> ScoreResult:
    contributions = [
        {"feature": feature, "impact": WEIGHTS[feature]}
        for feature in features if feature in WEIGHTS
    ]
    score = max(0, min(100, sum(item["impact"] for item in contributions)))
    return ScoreResult(score, contributions)


def combine_scores(owner_business: int, signal_identity: int, contradictions: int = 0) -> int:
    """Conservative conjunctive score: weak links cap the overall result.

    This intentionally is not a simple average. Identity resolution requires both
    propositions; contradictions add an explicit penalty.
    """
    base = min(owner_business, signal_identity)
    corroboration_bonus = 5 if owner_business >= 80 and signal_identity >= 80 else 0
    return max(0, min(100, base + corroboration_bonus - contradictions))
