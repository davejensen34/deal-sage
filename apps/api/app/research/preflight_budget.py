"""Pure reservation checks for the explicitly approved M7 source preflight."""

SLOTS = {
    "M7-CO-1": ("CO", "possible_death", "signal_first", "Colorado business owner obituary company"),
    "M7-UT-1": ("UT", "retirement", "signal_first", "Utah business owner retirement"),
    "M7-UT-2": ("UT", "succession", "hybrid", "Utah family business succession announcement"),
    "M7-CO-2": ("CO", "ownership_change", "hybrid", "Colorado privately held business ownership transfer"),
    "M7-TX-1": ("TX", "founder_exit", "signal_first", "Texas company founder departure"),
    "M7-UT-3": ("UT", "dissolution", "business_first", "Utah business dissolution public notice"),
    "M7-TX-2": ("TX", "restructuring", "business_first", "Texas private company restructuring announcement"),
    "M7-CO-3": ("CO", "leadership_change", "signal_first", "Colorado private company leadership change"),
}
PROTOCOL = "m7-source-preflight-v1"
SEARCH_RESERVATION_CENTS = 12


def reserve(calls: list[dict], slot: str, kind: str) -> dict:
    """Reservations survive failures; retries consume another request and budget.

    Each search reserves 12 cents: 400k input tokens at $0.25/M,
    1k output tokens at $2/M, and one $0.01 web tool call, rounded up.
    HTTP access checks and redirect attempts count toward the page ceiling too.
    The operational runner must serialize and persist this before network I/O.
    """
    if slot not in SLOTS or kind not in {"search", "http", "registry"}:
        raise ValueError("Unsupported preflight slot or action")
    caps = {"search": (2, 16), "http": (3, 24), "registry": (2, 2)}
    local, total = caps[kind]
    if sum(r["kind"] == kind and r["slot"] == slot for r in calls) >= local:
        raise ValueError("Slot request ceiling exhausted")
    if sum(r["kind"] == kind for r in calls) >= total:
        raise ValueError("Global request ceiling exhausted")
    if kind == "registry" and SLOTS[slot][0] == "UT":
        raise ValueError("Utah uses retained BEL only")
    cents = SEARCH_RESERVATION_CENTS if kind == "search" else 0
    if sum(r["reserved_cents"] for r in calls) + cents > 200:
        raise ValueError("Global cost ceiling exhausted")
    if sum(r["reserved_cents"] for r in calls if r["slot"] == slot) + cents > 25:
        raise ValueError("Slot cost ceiling exhausted")
    row = {"slot": slot, "kind": kind, "reserved_cents": cents, "status": "reserved"}
    calls.append(row)
    return row
