# Milestone 4 — Intelligent Business Discovery and Analysis

Status: proposed; gated by adequate curated evidence and Milestone 3.1 evaluation-contract quality.

## Goal

Use OpenAI and/or Anthropic to extract and analyze business details from curated evidence while keeping provenance, deterministic controls, and human review authoritative.

## Intended scope

- Productize the live-tested provider interface and runtime packaging first exercised in Milestone 3.1.
- Expand schema-constrained business-detail extraction, ambiguity and entity-match analysis, evidence synthesis, and bounded model-assisted next-source research planning.
- Require every claim to cite curated evidence and retain provider, model, task, prompt/schema version, timestamp, latency, token usage, cost where available, and outcome.
- Evaluate extraction quality, abstention, contradiction handling, reproducibility, latency, and cost against a human-labeled set.
- Present model output as proposed inference until reviewed; record acceptance, correction, or rejection.

## Boundary

Models do not calculate authoritative scores, silently mutate validated facts, approve identities, control workflow state, or bypass source restrictions. Milestone 4 does not begin until the available curated evidence and versioned evaluation contract are strong enough to measure output quality honestly; live connectivity alone is insufficient.
