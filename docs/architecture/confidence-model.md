# Explainable confidence model

Confidence scores are research prioritization signals, not assertions of fact.

The downstream `CandidateMatch` queue scores two propositions independently: whether a person controlled a business, and whether a transition signal refers to that person. Its overall score is conjunctive: the weaker proposition caps the result. A five-point corroboration bonus applies only when both component scores are at least 80; explicit contradiction penalties are then subtracted. This is not an unexplained average.

Feature weights live in `app/domain/scoring.py`. Positive examples include owner filing +25, exact full name +15, same city +12, address overlap +12, company named in signal +10, independent source +10, aligned age +8, relative overlap +7, and aligned timeline +7. Negative examples include registered-agent-only −35, former owner −30, age contradiction −28, geographic conflict −24, common name −15, insufficient diversity −12, and stale source −8.

Scores are clamped to 0–100. Suggested queue thresholds are high priority ≥80, review 60–79, and weak <60. Candidate status is always a separate analyst decision.

Earlier unresolved `ResearchCase` work uses a separate versioned confidence contract with five axes: business identity, owner relationship, transition identity, operating status, and overall opportunity. Every assessment preserves its claim factors, adjustments, independence grouping, and contradiction penalties. Overall opportunity is conjunctive across the three identity/relationship axes and is capped when the business is inactive or dissolved. This case-level contract does not overwrite the later candidate decision.

Current limitation: the candidate scoring engine and tests exist, while seeded `CandidateMatch` scores are curated fixtures chosen to demonstrate edge cases rather than recalculated from persisted feature observations. Research-case confidence factors are persisted and tested, but the demo UI is not a production calibration study. Production candidate scoring still requires persisted feature observations and a recalculation service.
