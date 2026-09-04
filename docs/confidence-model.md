# Explainable confidence model

Confidence scores are research prioritization signals, not assertions of fact.

DealSage scores two propositions independently: whether a person controlled a business, and whether a transition signal refers to that person. The overall score is deliberately conjunctive: the weaker proposition caps the result. A five-point corroboration bonus applies only when both component scores are at least 80, and explicit contradiction penalties are then subtracted. This is not an unexplained average.

Configuration-driven feature weights live in `app/domain/scoring.py`. Positive examples include owner filing +25, exact full name +15, same city +12, address overlap +12, company named in signal +10, an independent source +10, aligned age +8, relative overlap +7, and timeline alignment +7. Negative examples include registered-agent-only −35, former owner −30, age contradiction −28, geographic conflict −24, common name −15, insufficient evidence diversity −12, and stale source −8.

Scores are clamped to 0–100. Suggested queue thresholds are high priority ≥80, review 60–79, and weak <60. Status is always a separate analyst decision.

Limitations: weights encode transparent product judgment, not statistical calibration; missing public records can depress scores; records can be stale or wrong; correlated sources may not be independent; uncommon names can still collide; no score proves identity, ownership, death, or transition. Human review is mandatory for ambiguous cases.
