import json
from pathlib import Path

import pytest

from app.ai.providers.base import AIProvider, AIProviderIncompleteError, AIProviderRefusalError, TokenUsage
from app.research.model_evaluation import consistency_errors, evaluate_output, failed_evaluation
from scripts.run_milestone31_model_validation import run_comparison, validate_live_authorization


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "milestone31_evaluation_v2.json"


class FixtureProvider(AIProvider):
    def __init__(self, outputs, failure=None):
        self.outputs = outputs
        self.failure = failure
        self.model = "fixture-model"
        self.last_usage = TokenUsage()
        self.last_token_usage = None

    async def extract_structured(self, text, schema):
        packet = json.loads(text.split("\n\n", 1)[1])
        self.last_usage = TokenUsage(input_tokens=20, output_tokens=10, total_tokens=30)
        self.last_token_usage = 30
        if self.failure:
            raise self.failure
        return self.outputs[packet["case_id"]]

    async def summarize(self, context):
        return "fixture"

    async def analyze_match(self, context):
        return {"summary": "fixture"}


def load_cases():
    return json.loads(FIXTURE_PATH.read_text())["cases"]


@pytest.mark.asyncio
async def test_all_fictional_case_shapes_match_each_dimension_with_adapter_mocks():
    cases = load_cases()
    outputs = {case["case_id"]: case["expected_output"] for case in cases}
    providers = {"openai": FixtureProvider(outputs), "anthropic": FixtureProvider(outputs)}

    records, metrics = await run_comparison(cases, providers)

    assert len(records) == 14
    assert metrics["provider_outcomes"] == {"completed": 14, "incomplete": 0, "refusal": 0, "invalid": 0, "failed": 0}
    assert all(value == {"evaluated": 14, "matches": 14, "accuracy": 1.0} for value in metrics["dimension_metrics"].values())
    assert metrics["tokens"] == {"input": 280, "output": 140, "total": 420}
    assert metrics["by_provider"]["openai"]["dimension_metrics"]["relationship"] == {
        "evaluated": 7,
        "matches": 7,
        "accuracy": 1.0,
    }
    assert records[0]["usage"] == {"input_tokens": 20, "output_tokens": 10, "total_tokens": 30}


def test_former_owner_and_active_business_are_independent_dimensions():
    case = load_cases()[0]
    result = evaluate_output(
        case["expected_output"],
        case["expected_dimensions"],
        {"F01-S1"},
        TokenUsage(),
    )

    assert result.provider_outcome == "completed"
    assert result.output["relationship"] == "former_owner"
    assert result.output["operating_status"] == "active"


def test_business_first_resolution_can_leave_successor_unknown():
    case = load_cases()[1]
    result = evaluate_output(
        case["expected_output"],
        case["expected_dimensions"],
        {"F02-S1"},
        TokenUsage(),
    )

    assert result.output["case_origin"] == "business_first"
    assert result.output["identity_resolution"] == "resolved"
    assert "successor is unknown" in result.output["unresolved_questions"][0].lower()
    assert result.output["research_disposition"] == "needs_more_research"


def test_internal_output_contradictions_are_detected_deterministically():
    output = load_cases()[2]["expected_output"] | {
        "relationship": "former_owner",
        "relationship_time": "current_at_signal",
        "contradictions": ["conflict"],
    }

    assert consistency_errors(output, {"F03-S1"}) == [
        "relationship_time_conflicts_with_relationship",
        "contradictions_present_when_state_is_none",
        "candidate_supported_without_required_resolved_dimensions",
        "research_disposition_conflicts_with_dimension_precedence",
    ]


@pytest.mark.parametrize(
    ("error", "outcome"),
    [
        (AIProviderIncompleteError("max_tokens"), "incomplete"),
        (AIProviderRefusalError("policy"), "refusal"),
        (ValueError("invalid json"), "invalid"),
        (RuntimeError("network"), "failed"),
    ],
)
def test_provider_failures_are_not_negative_classifications(error, outcome):
    result = failed_evaluation(error, TokenUsage(input_tokens=4, output_tokens=1, total_tokens=5))

    assert result.provider_outcome == outcome
    assert result.dimension_matches is None
    assert result.output is None


@pytest.mark.asyncio
async def test_failure_metrics_exclude_failed_paths_from_dimension_denominators():
    cases = load_cases()[:1]
    outputs = {case["case_id"]: case["expected_output"] for case in cases}
    providers = {
        "openai": FixtureProvider(outputs, AIProviderIncompleteError("max_tokens")),
        "anthropic": FixtureProvider(outputs),
    }

    _, metrics = await run_comparison(cases, providers)

    assert metrics["provider_outcomes"]["incomplete"] == 1
    assert metrics["provider_outcomes"]["completed"] == 1
    assert all(value["evaluated"] == 1 for value in metrics["dimension_metrics"].values())
    assert metrics["by_provider"]["openai"]["dimension_metrics"]["case_origin"]["evaluated"] == 0
    assert metrics["by_provider"]["openai"]["dimension_metrics"]["case_origin"]["accuracy"] is None


def test_live_runner_rejects_the_exhausted_v1_protocol():
    with pytest.raises(ValueError, match="version-two"):
        validate_live_authorization({"schema_version": "milestone-3-1-comparison-v1"}, "issue-53")


def test_live_runner_requires_the_recorded_protocol_decision():
    manifest = {"schema_version": "milestone-3-1-comparison-v2", "protocol_decision": "future-approved-id"}

    with pytest.raises(ValueError, match="same approved protocol"):
        validate_live_authorization(manifest, "different-id")
