import pytest
from app.research.recent_discovery import MODEL
from scripts.milestone7_completion import candidate_clues


def response(status="incomplete", reason="max_output_tokens", model=MODEL):
    return {"status": status, "model": model, "incomplete_details": {"reason": reason},
            "output": [{"type": "web_search_call", "action": {"type": "search", "sources": [
                {"type": "url", "url": "https://example.com/company", "title": "Example company"}]}}]}


def test_truncated_narrative_retains_untrusted_consulted_source():
    clues = candidate_clues(response())
    assert len(clues) == 1
    assert clues[0]["access_observations"]["access_review_required"] is True
    assert clues[0]["url"] == "https://example.com/company"


@pytest.mark.parametrize("kwargs", [{"reason": "content_filter"}, {"status": "failed"}, {"model": "other"}])
def test_unexpected_response_never_becomes_a_clue(kwargs):
    with pytest.raises(ValueError):
        candidate_clues(response(**kwargs))
