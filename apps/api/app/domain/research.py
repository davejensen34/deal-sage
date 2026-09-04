from collections import Counter
from typing import Iterable

from app.domain.models import BusinessRelationship, ResearchStage

STAGE_ORDER = (
    "target_profile", "business_discovered", "entity_anchored",
    "business_identity_validated", "web_presence_validated",
    "person_discovered", "relationship_validated", "owner_research_ready",
)
CONTROLLING_ROLES = {"owner", "co_owner", "member", "managing_member", "partner"}


def owner_readiness(relationship: BusinessRelationship, stages: Iterable[ResearchStage]) -> tuple[bool, str]:
    """Gate expensive transition research on explicit role evidence and a validated trail."""
    stage_map = {stage.stage_type: stage for stage in stages}
    required = ("business_identity_validated", "web_presence_validated", "relationship_validated")
    if relationship.relationship_type not in CONTROLLING_ROLES:
        return False, f"{relationship.relationship_type.replace('_', ' ').title()} does not establish current control."
    if relationship.confidence < 0.75:
        return False, "Owner/business confidence is below the 75% research threshold."
    incomplete = [name for name in required if stage_map.get(name) is None or stage_map[name].status != "validated"]
    if incomplete:
        return False, f"Required stages are not validated: {', '.join(incomplete)}."
    return True, "Explicit controlling role, sufficient confidence, and corroborated business/web/relationship stages."


def funnel_counts(stages: Iterable[ResearchStage]) -> list[dict[str, int | str]]:
    # Count persisted stage outcomes; never extrapolate conversion percentages.
    counts = Counter(stage.stage_type for stage in stages if stage.status == "validated")
    return [{"stage": stage, "count": counts[stage]} for stage in STAGE_ORDER]
