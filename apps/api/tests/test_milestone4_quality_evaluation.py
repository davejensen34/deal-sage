from scripts.run_milestone4_quality_evaluation import ProtocolStop, _case_result


def test_protocol_stop_preserves_partial_case_without_model_output():
    case = {
        "slot": "M4-CO-1",
        "prelabel": {"research_disposition": "no_business_found"},
        "query": "bounded query",
    }
    partial = _case_result(
        case,
        7,
        [],
        [{"url": "https://example.test", "status": "failed", "error_class": "HTTPStatusError"}],
        [],
    )

    stopped = ProtocolStop("qualified_source_failed:HTTPStatusError", partial)

    assert stopped.reason == "qualified_source_failed:HTTPStatusError"
    assert stopped.partial_case["slot"] == "M4-CO-1"
    assert stopped.partial_case["proposals"] == []
