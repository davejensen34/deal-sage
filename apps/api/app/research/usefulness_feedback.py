"""Offline validation of self-reported reviews, never human authentication."""

from collections import Counter
from datetime import datetime
from hashlib import sha256
import json
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.research.transition_evaluation import ratio


PACKAGE_SHA256 = "e76bb18c0d421a622c73fcdcbe1966957a3b2eb0047877aa7e4327cec3d54749"
# September 14 corrective cohort, separately frozen after source/date review.
# The original failed-value cohort remains accepted and cannot be mixed with it.
COMPLETION_PACKAGE_SHA256 = "9b8db67e21342f64fc25d67dba3005daac72536b30719610361a635f36ad2bbe"
MAX_BYTES = 2_000_000


class Judgment(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    slot: str
    usefulness: Literal["useful", "not_useful", "defer"]
    rationale: str = Field(min_length=3, max_length=4000)
    self_reported_review_seconds: int | None = Field(ge=0, le=86400)

    @field_validator("rationale")
    @classmethod
    def meaningful_rationale(cls, value):
        if len(value.strip()) < 3:
            raise ValueError("Missing rationale")
        return value


class Feedback(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    version: Literal["m7-human-usefulness-v1"]
    package_sha256: str
    result_sha256: str
    bundle_sha256: str
    reviewer: str = Field(min_length=1, max_length=200)
    attribution: Literal["self_reported_human"]
    recorded_at: str
    judgments: list[Judgment] = Field(min_length=1, max_length=20)
    unreviewed_slots: list[str] = Field(max_length=20)
    analyst_acceptance: None
    time_saved_seconds: None
    promotions: Literal[0]

    @field_validator("promotions", mode="before")
    @classmethod
    def no_promotions(cls, value):
        if type(value) is not int or value != 0:
            raise ValueError("Invalid promotion boundary")
        return value

    @field_validator("recorded_at")
    @classmethod
    def dated_attribution(cls, value):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("Timestamp requires a timezone")
        return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("Non-finite JSON number")


def _json(raw: bytes):
    if len(raw) > MAX_BYTES:
        raise ValueError("Review file exceeds size limit")
    try:
        return json.loads(raw, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise ValueError("Invalid review JSON") from None


def summarize_feedback(package_bytes: bytes, feedback_files: list[bytes]) -> dict:
    """Bind explicit input files, reject double counting, and expose denominators.

    A name is self-reported. Matching names normalize Unicode/case/whitespace to
    avoid accidental duplicate reviewer-slot judgments, not to establish identity.
    Conflicting exports require deliberate file selection; no 'latest wins' rule
    silently replaces prior feedback. No raw rationale enters aggregate output.
    """
    package_hash = sha256(package_bytes).hexdigest()
    if package_hash not in {PACKAGE_SHA256, COMPLETION_PACKAGE_SHA256}:
        raise ValueError("Unreviewed analyst package")
    package = _json(package_bytes)
    slots = {item["slot"] for item in package["items"]}
    if len(feedback_files) > 100:
        raise ValueError("Too many feedback files")
    seen, records, hashes = set(), [], []
    for raw in feedback_files:
        try:
            feedback = Feedback.model_validate(_json(raw))
        except (ValidationError, ValueError, TypeError):
            # Pydantic errors include original values: exclude them from logs.
            raise ValueError("Invalid feedback contract") from None
        if any(getattr(feedback, key) != expected for key, expected in (
            ("package_sha256", package_hash), ("result_sha256", package["result_sha256"]),
            ("bundle_sha256", package["bundle_sha256"]),
        )):
            raise ValueError("Feedback fingerprint mismatch")
        reviewer = " ".join(unicodedata.normalize("NFKC", feedback.reviewer).casefold().split())
        if not reviewer:
            raise ValueError("Missing reviewer attribution")
        reviewed = [j.slot for j in feedback.judgments]
        missing = feedback.unreviewed_slots
        if (len(set(reviewed)) != len(reviewed) or len(set(missing)) != len(missing)
                or set(reviewed) & set(missing) or set(reviewed) | set(missing) != slots):
            raise ValueError("Feedback slot partition mismatch")
        digest = sha256(raw).hexdigest()
        hashes.append(digest)
        for judgment in feedback.judgments:
            key = (reviewer, judgment.slot)
            if key in seen:
                raise ValueError("Duplicate reviewer-slot judgment; select intended exports")
            seen.add(key)
            records.append((reviewer, judgment))
    counts = Counter(j.usefulness for _, j in records)
    durations = [j.self_reported_review_seconds for _, j in records if j.self_reported_review_seconds is not None]
    reviewed_slots = {j.slot for _, j in records}
    return {
        "version": "m7-usefulness-summary-v1", "package_sha256": package_hash,
        "result_sha256": package["result_sha256"], "bundle_sha256": package["bundle_sha256"],
        "feedback_sha256": sorted(hashes), "attribution": "self_reported_human_not_authenticated",
        "reviewer_labels": len({reviewer for reviewer, _ in records}),
        "judgments": len(records), "judgment_counts": {k: counts[k] for k in ("useful", "not_useful", "defer")},
        "packet_review_coverage": ratio(len(reviewed_slots), len(slots)),
        "judgment_usefulness": ratio(counts["useful"], len(records)),
        "unreviewed_slots": sorted(slots - reviewed_slots),
        "per_packet": [{"slot": slot, "judgment_counts": dict(Counter(j.usefulness for _, j in records if j.slot == slot))}
                       for slot in sorted(slots)],
        "self_reported_review_seconds": {"measured": len(durations), "missing": len(records)-len(durations),
                                         "known_total": sum(durations) if durations else None},
        "time_saved_seconds": None, "promotion_precision": None, "analyst_acceptance": None,
        "milestone_complete": False, "external_calls": 0,
    }
