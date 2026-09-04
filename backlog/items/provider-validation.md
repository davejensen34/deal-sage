# Validate model providers for bounded discovery and analysis

Status: proposed for Milestone 4 · Priority: P1 within Milestone 4

Problem: OpenAI and Anthropic summary adapters exist but have not been exercised live, structured extraction is unimplemented, and the Docker image omits optional provider SDKs. Model-assisted discovery must not run directly against uncurated source material.

Outcome: after Milestone 3 provides curated evidence, validate at least one provider end to end; add schema-constrained business-detail extraction, ambiguity and match analysis, evidence synthesis, and bounded research planning. Record model and prompt identity, evidence references, latency, token usage, cost where available, result, and analyst disposition. Make intentional Docker support explicit and run bounded live checks only when credentials and product need justify cost.

All model output remains labeled inference and evidence-bounded. Deterministic code retains authority over validation, persistence transitions, and scores; a human must review proposed business facts before they become authoritative.
