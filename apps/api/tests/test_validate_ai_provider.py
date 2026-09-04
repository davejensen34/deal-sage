from scripts.validate_ai_provider import is_ready_response


def test_ready_response_allows_only_cosmetic_variation():
    assert is_ready_response("Provider ready.")
    assert is_ready_response("  PROVIDER   READY!  ")
    assert not is_ready_response("The provider should be ready")
    assert not is_ready_response("")
