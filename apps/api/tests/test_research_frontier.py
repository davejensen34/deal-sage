from datetime import datetime, timedelta, timezone

import pytest

from app.research.cases import ResearchCaseService
from app.research.frontier import ResearchPlanner


def make_case(db, **budget):
    return ResearchCaseService(db).create_case(
        "signal_first",
        {
            "max_queries": 2,
            "max_documents": 2,
            "max_model_calls": 1,
            "max_steps": 3,
            "max_elapsed_seconds": 300,
            "max_cost_cents": 10,
            **budget,
        },
    )


def add_item(planner, case_id, *, priority=50, max_attempts=2):
    return planner.add_item(
        case_id,
        question_type="verify_relationship",
        question="Did the source describe a current ownership relationship?",
        rationale="Employment and ownership must remain distinct.",
        priority=priority,
        max_attempts=max_attempts,
    )


def test_planner_prioritizes_and_records_a_reconstructable_step(override_db_session):
    case = make_case(override_db_session)
    planner = ResearchPlanner(override_db_session)
    lower = add_item(planner, case.id, priority=20)
    higher = add_item(planner, case.id, priority=90)

    assert planner.next_item(case.id).id == higher.id
    step = planner.start_step(
        case.id, higher.id, action_type="search", provider="fixture-search"
    )
    completed = planner.complete_step(
        step.id,
        outcome="succeeded",
        result_summary={"candidate_count": 2},
        resolves_item=True,
    )

    assert completed.step_number == 1
    assert completed.provider == "fixture-search"
    assert completed.result_summary == {"candidate_count": 2}
    assert planner.next_item(case.id).id == lower.id


def test_empty_and_resolved_frontiers_stop_explicitly(override_db_session):
    empty_case = make_case(override_db_session)
    planner = ResearchPlanner(override_db_session)
    assert planner.next_item(empty_case.id) is None
    assert empty_case.stop_reason == "frontier_empty"

    resolved_case = make_case(override_db_session)
    item = add_item(planner, resolved_case.id)
    step = planner.start_step(resolved_case.id, item.id, action_type="analyze")
    planner.complete_step(step.id, outcome="succeeded", resolves_item=True)
    assert planner.next_item(resolved_case.id) is None
    assert resolved_case.stop_reason == "frontier_resolved"


def test_attempt_limit_becomes_a_visible_stop(override_db_session):
    case = make_case(override_db_session)
    planner = ResearchPlanner(override_db_session)
    item = add_item(planner, case.id, max_attempts=1)
    step = planner.start_step(
        case.id, item.id, action_type="retrieve", provider="fixture-retriever"
    )
    planner.complete_step(step.id, outcome="failed", error_class="TimeoutError")

    assert planner.next_item(case.id) is None
    assert case.stop_reason == "frontier_attempts_exhausted"


def test_running_step_does_not_look_like_frontier_exhaustion(override_db_session):
    case = make_case(override_db_session)
    planner = ResearchPlanner(override_db_session)
    item = add_item(planner, case.id)
    planner.start_step(case.id, item.id, action_type="analyze")

    assert planner.next_item(case.id) is None
    assert case.status == "open"
    assert case.stop_reason is None


def test_model_provenance_and_action_budgets_are_authoritative(override_db_session):
    case = make_case(override_db_session, max_model_calls=0)
    planner = ResearchPlanner(override_db_session)
    item = add_item(planner, case.id)

    with pytest.raises(ValueError, match="provider, model, and prompt"):
        planner.start_step(case.id, item.id, action_type="model_analysis", provider="openai")
    with pytest.raises(ValueError, match="model_budget_exhausted"):
        planner.start_step(
            case.id,
            item.id,
            action_type="model_analysis",
            provider="openai",
            model="example-model",
            prompt_version="research-plan-v1",
        )
    assert case.stop_reason == "model_budget_exhausted"


@pytest.mark.parametrize(
    ("limit", "action", "reason"),
    [
        ("max_queries", "search", "query_budget_exhausted"),
        ("max_documents", "retrieve", "document_budget_exhausted"),
    ],
)
def test_zero_action_budgets_stop_before_execution(
    override_db_session, limit, action, reason
):
    case = make_case(override_db_session, **{limit: 0})
    planner = ResearchPlanner(override_db_session)
    item = add_item(planner, case.id)
    with pytest.raises(ValueError, match=reason):
        planner.start_step(case.id, item.id, action_type=action, provider="fixture")
    assert case.stop_reason == reason


def test_step_budget_stops_before_frontier_selection(override_db_session):
    case = make_case(override_db_session, max_steps=0)
    planner = ResearchPlanner(override_db_session)
    add_item(planner, case.id)
    assert planner.next_item(case.id) is None
    assert case.stop_reason == "step_budget_exhausted"


def test_time_and_cost_budgets_stop_before_another_action(override_db_session):
    cost_case = make_case(override_db_session, max_cost_cents=2)
    planner = ResearchPlanner(override_db_session)
    item = add_item(planner, cost_case.id)
    step = planner.start_step(cost_case.id, item.id, action_type="analyze")
    planner.complete_step(step.id, outcome="succeeded", cost_cents=2)
    assert planner.next_item(cost_case.id) is None
    assert cost_case.stop_reason == "cost_budget_exhausted"

    time_case = make_case(override_db_session, max_elapsed_seconds=1)
    time_case.created_at = datetime.now(timezone.utc) - timedelta(seconds=2)
    override_db_session.commit()
    add_item(planner, time_case.id)
    assert planner.next_item(time_case.id) is None
    assert time_case.stop_reason == "time_budget_exhausted"


def test_cross_case_claims_and_unsafe_results_are_rejected(override_db_session):
    cases = ResearchCaseService(override_db_session)
    first = make_case(override_db_session)
    second = make_case(override_db_session)
    evidence = cases.add_evidence(
        first.id,
        source_mode="case_specific_research",
        canonical_url="https://example.test/source",
        publisher="Example",
        source_type="obituary",
        content=b"Morgan owned Example Works.",
        relevant_excerpt="Morgan owned Example Works.",
        extracted_facts={},
        provenance={},
    )
    claim = cases.add_claim(
        first.id,
        evidence.id,
        subject_type="relationship",
        predicate="relationship",
        object_value={"business_name": "Example Works"},
        relationship_semantics="owner",
        confidence=1,
        classification="source_fact",
        source_authority="publisher",
        directness="direct_statement",
    )
    planner = ResearchPlanner(override_db_session)
    with pytest.raises(ValueError, match="same research case"):
        planner.add_item(
            second.id,
            question_type="verify_relationship",
            question="Does this claim belong here?",
            rationale="Cross-case lineage must be rejected.",
            priority=50,
            supporting_claim_ids=[claim.id],
        )

    item = add_item(planner, second.id)
    step = planner.start_step(second.id, item.id, action_type="analyze")
    with pytest.raises(ValueError, match="Forbidden source field"):
        planner.complete_step(
            step.id,
            outcome="failed",
            result_summary={"session_token": "must-not-persist"},
            error_class="RuntimeError",
        )
    with pytest.raises(ValueError, match="exception class"):
        planner.complete_step(
            step.id,
            outcome="failed",
            error_class="RuntimeError: secret provider body",
        )


def test_analyst_can_stop_when_safe_research_is_unavailable(override_db_session):
    case = make_case(override_db_session)
    stopped = ResearchPlanner(override_db_session).stop_case(
        case.id, "safe_research_unavailable"
    )
    assert stopped.status == "stopped"
    assert stopped.stop_reason == "safe_research_unavailable"


def test_unknown_budget_dimensions_are_rejected(override_db_session):
    with pytest.raises(ValueError, match="unsupported limits"):
        ResearchCaseService(override_db_session).create_case(
            "signal_first", {"unbounded_provider_calls": 999}
        )
