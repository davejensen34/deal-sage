# Validate model providers for bounded discovery and analysis

Status: partially implemented in Milestone 3.1; remaining productization is proposed for Milestone 4 · Priority: P1 within Milestone 4

Observed foundation: OpenAI and Anthropic adapters now provide bounded summaries and native schema-constrained extraction, the Compose API image includes both SDKs, synthetic connectivity succeeded for both providers, and the approved seven-case public-evidence cohort was executed. The corrected run produced 12/14 parseable outputs but only 3/14 matched the conflated top-level pre-label; two OpenAI paths ended without parseable output. These failures are recorded in `docs/research/milestone-3-1-live-validation-results.md` and are not a quality-validation claim.

Remaining outcome: first replace the version-one evaluation outcome with separate origin, identity, relationship/timeline, operating-status, and contradiction dimensions; add explicit incomplete/refusal handling and separate input/output token accounting; then validate that contract against saved synthetic fixtures. Milestone 4 can productize business-detail extraction, ambiguity and match analysis, evidence synthesis, and model-assisted research planning only after the evidence and evaluation contracts are adequate. Record model and prompt identity, evidence references, latency, token usage, cost where available, result, and analyst disposition.

All model output remains labeled inference and evidence-bounded. Deterministic code retains authority over validation, persistence transitions, and scores; a human must review proposed business facts before they become authoritative.
