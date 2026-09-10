# Persist evidence-derived scoring features

Status: implemented and validated in Milestone 5 Issue #95 / PR #101

Problem: deterministic scoring exists, but demo scores are curated fixtures rather than reproduced from persisted feature observations.

Outcome: persist feature observations and score versions; recalculate all three scores deterministically; show exact contributions; audit recalculation. Validation must cover contradictions, registered-agent-only cases, and version changes. No model may author the authoritative score.

Result: immutable `CandidateScoreAssessment` records retain method version, provenance classification, component inputs, contradiction penalty, factors, supporting evidence IDs, calculation, and result. Evidence-derived review-queue promotion recalculates and projects the deterministic score; seeded fixtures remain explicitly labeled `legacy_demo_import`. Model output cannot author the score.
