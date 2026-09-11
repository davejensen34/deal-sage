import pytest
from app.research.preflight_budget import reserve, SLOTS


def test_full_search_envelope_fits_without_releasing_reservations():
    calls = []
    for slot in SLOTS:
        for _ in range(2):
            reserve(calls, slot, "search")["status"] = "failed"
    assert sum(r["reserved_cents"] for r in calls) == 192
    with pytest.raises(ValueError):
        reserve(calls, "M7-CO-1", "search")


def test_access_checks_and_redirects_also_consume_http_slots():
    calls = []
    for _ in range(3):
        reserve(calls, "M7-CO-1", "http")
    with pytest.raises(ValueError):
        reserve(calls, "M7-CO-1", "http")


def test_registry_ceiling_and_utah_delivery_boundary():
    calls = []
    reserve(calls, "M7-CO-1", "registry")
    reserve(calls, "M7-TX-1", "registry")
    with pytest.raises(ValueError):
        reserve(calls, "M7-CO-2", "registry")
    with pytest.raises(ValueError):
        reserve([], "M7-UT-1", "registry")


@pytest.mark.parametrize("calls,slot", [
    ([{"slot":"M7-CO-1","kind":"http","reserved_cents":20}], "M7-CO-1"),
    ([{"slot":"M7-CO-1","kind":"http","reserved_cents":195}], "M7-TX-1"),
])
def test_cost_reservations_fail_before_mutation(calls, slot):
    with pytest.raises(ValueError):
        reserve(calls, slot, "search")
    assert len(calls) == 1
