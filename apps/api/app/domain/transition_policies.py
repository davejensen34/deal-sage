"""Versioned research guidance, not evidence, scores, or promotion permission."""

from dataclasses import asdict, dataclass


POLICY_VERSION = "transition-policy-v1"


@dataclass(frozen=True)
class TransitionPolicy:
    signal_type: str
    label: str
    subject_type: str
    evidence_requirements: tuple[str, ...]
    temporal_questions: tuple[str, ...]
    ownership_limitations: tuple[str, ...]
    review_questions: tuple[str, ...]


# These are questions to resolve through retained evidence and analyst review.
# In particular, an announcement does not establish that its event completed.
_POLICIES = (
    TransitionPolicy(
        "possible_death", "Possible death", "person",
        ("Retain the reported death and identify its subject beyond name alone.",),
        ("When was the death reported to occur, separately from publication?",),
        ("Death does not identify a successor or establish current business control.",),
        ("What connects this person to the business at the event date?",),
    ),
    TransitionPolicy(
        "retirement", "Retirement", "person",
        ("Retain an explicit retirement statement and the role it concerns.",),
        ("Is retirement planned, effective, postponed, or historical?",),
        ("Retirement from employment or management does not prove an ownership exit.",),
        ("Does the person retain equity or control after leaving the role?",),
    ),
    TransitionPolicy(
        "succession", "Succession", "person_business_relationship",
        ("Retain the stated predecessor, successor, business and affected role.",),
        ("Is succession proposed, underway, or completed, and when?",),
        ("Management succession does not establish transfer of ownership.",),
        ("What evidence distinguishes the successor's role from equity or control?",),
    ),
    TransitionPolicy(
        "ownership_change", "Ownership transfer", "person_business_relationship",
        ("Retain explicit transfer evidence identifying the business and parties.",),
        ("Was the transfer announced or completed, and on what effective date?",),
        ("A proposed sale or asset transfer does not prove a completed change of control.",),
        ("What interest transferred, to whom, and with what remaining control?",),
    ),
    TransitionPolicy(
        "founder_exit", "Founder exit", "person",
        ("Retain an explicit departure statement and evidence of the founder role.",),
        ("When does the departure take effect and which roles end?",),
        ("Founder status and executive departure do not establish former ownership.",),
        ("Does the founder retain shares, board rights, or another controlling role?",),
    ),
    TransitionPolicy(
        "dissolution", "Dissolution", "business",
        ("Retain entity-specific dissolution evidence and the exact jurisdiction.",),
        ("Is dissolution proposed, effective, reversed, or followed by reinstatement?",),
        ("Legal dissolution does not establish an owner's exit or cessation of every operation.",),
        ("Does the record refer to this legal entity rather than a namesake or affiliate?",),
    ),
    TransitionPolicy(
        "restructuring", "Restructuring", "business",
        ("Retain the stated restructuring action and affected legal entities.",),
        ("Which restructuring steps are planned versus effective?",),
        ("Restructuring does not necessarily transfer ownership or indicate distress.",),
        ("What changed in equity, control, liabilities, or operations?",),
    ),
    TransitionPolicy(
        "leadership_change", "Leadership change", "person_business_relationship",
        ("Retain the appointment or departure statement and the exact role.",),
        ("What is the role's effective start or end date?",),
        ("Executive and registered-agent roles never automatically imply ownership.",),
        ("Is there separate evidence of an ownership or control change?",),
    ),
)


def transition_policy(signal_type: str) -> TransitionPolicy:
    """Resolve a canonical type; never reinterpret unknown historical records."""
    for policy in _POLICIES:
        if policy.signal_type == signal_type:
            return policy
    raise ValueError(f"Unsupported transition signal type: {signal_type}")


def transition_policy_catalog() -> dict:
    """Return a detached representation so consumers cannot mutate the catalog."""
    return {
        "version": POLICY_VERSION,
        "classification": "research_guidance",
        "limitations": [
            "Policies are not source facts, calibrated confidence, or promotion approval.",
            "Unverified clues remain investigable with provenance and access restrictions.",
            "Resolve identity beyond name alone and retain contradictory evidence.",
            "Unknown dates remain unknown; publication is not the event date.",
            "Source evidence, DealSage inference, and human decisions remain separate.",
            "Live source activation requires a separately approved bounded evaluation.",
        ],
        "policies": [asdict(policy) for policy in _POLICIES],
    }
