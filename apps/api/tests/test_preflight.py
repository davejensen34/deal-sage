from copy import deepcopy

import pytest

from app.research.preflight import exact_excerpt, validate_candidate_manifest, visible_text


@pytest.fixture
def manifest():
    def case(state, origin):
        return {
            "state": state,
            "origin": origin,
            "sources": [
                {
                    "url": f"https://example.test/{state}/one",
                    "publisher": "Publisher one",
                    "source_type": "newspaper",
                    "excerpt": "Direct source sentence.",
                },
                {
                    "url": f"https://example.test/{state}/two",
                    "publisher": "Publisher two",
                    "source_type": "business_website",
                    "excerpt": "Independent source sentence.",
                },
            ],
        }

    return {
        "schema_version": "milestone-4-7-preflight-candidates-v1",
        "cases": [case("CO", "signal_first"), case("UT", "business_first"), case("TX", "hybrid")],
    }


def test_candidate_manifest_requires_state_origin_shape(manifest):
    validate_candidate_manifest(manifest)
    changed = deepcopy(manifest)
    changed["cases"][1]["origin"] = "signal_first"
    with pytest.raises(ValueError, match="fixed state"):
        validate_candidate_manifest(changed)


def test_candidate_manifest_requires_two_complete_https_sources(manifest):
    changed = deepcopy(manifest)
    changed["cases"][0]["sources"] = changed["cases"][0]["sources"][:1]
    with pytest.raises(ValueError, match="at least two"):
        validate_candidate_manifest(changed)
    changed = deepcopy(manifest)
    changed["cases"][2]["sources"][0]["url"] = "http://example.test"
    with pytest.raises(ValueError, match="HTTPS"):
        validate_candidate_manifest(changed)


def test_excerpt_must_exist_in_script_free_visible_text():
    page = visible_text("<style>hidden</style><p>Direct &amp; exact sentence.</p>")
    assert exact_excerpt(page, "Direct & exact sentence.") == "Direct & exact sentence."
    with pytest.raises(ValueError, match="absent"):
        exact_excerpt(page, "Search snippet only")
