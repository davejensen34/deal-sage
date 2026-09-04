# AI strategy

Use models only when they materially improve unstructured extraction, contextual interpretation, ambiguity analysis, evidence synthesis, or research planning. Deterministic code owns scoring arithmetic, validation, persistence, audit behavior, filtering, and state changes.

An `AIProvider` boundary defines extraction, summarization, and match-analysis capabilities. OpenAI and Anthropic adapters implement bounded summarization and JSON-Schema-validated structured extraction. Candidate evidence summary is optional, versioned, logged, evidence-bounded, and forbidden from changing confidence scores.

The local Compose image includes both optional SDKs but provider use remains disabled without an explicit provider and its key. Requests have timeout and output-token limits. OpenAI response storage is explicitly disabled because evidence packets can contain personal information. Provider exception bodies are not persisted because they may echo submitted evidence or request metadata. A synthetic smoke command requires an explicit live-call flag and makes exactly one call; automated tests never spend API credits.

Actual validation state: credential-free operation and adapter request construction are tested without network access. Local synthetic calls validated connectivity to OpenAI `gpt-5-mini` and Anthropic `claude-sonnet-4-5`. Both providers then processed the same approved seven-case public-evidence cohort using native structured-output paths. On the corrected and final allowed attempt, Anthropic returned 7/7 schema-valid results and OpenAI returned 5/7; only 3/14 top-level labels matched the pre-label because the version-one taxonomy conflated independent case dimensions. This validates connectivity, bounded execution, and parts of the integration contract, not comparative reasoning quality. See the [validation results](../research/milestone-3-1-live-validation-results.md).

Before another live cohort, the evaluation contract must separate case origin, identity resolution, relationship/timeline, operating status, and contradiction state; represent incomplete/refusal outcomes explicitly; and retain separate input/output token usage. The approved cohort has reached its call ceiling and cannot be rerun without a new explicit protocol decision.

Never store hidden chain-of-thought. Retain structured results, useful analyst-facing rationale, provider/model/task/prompt version, timestamp, latency, token usage when available, and outcome.
