# AI strategy

Use models only when they materially improve unstructured extraction, contextual interpretation, ambiguity analysis, evidence synthesis, or research planning. Deterministic code owns scoring arithmetic, validation, persistence, audit behavior, filtering, and state changes.

An `AIProvider` boundary defines extraction, summarization, and match-analysis capabilities. OpenAI and Anthropic adapters implement bounded summarization and JSON-Schema-validated structured extraction. Candidate evidence summary is optional, versioned, logged, evidence-bounded, and forbidden from changing confidence scores.

The local Compose image includes both optional SDKs but provider use remains disabled without an explicit provider and its key. Requests have timeout and output-token limits. OpenAI response storage is explicitly disabled because evidence packets can contain personal information. Provider exception bodies are not persisted because they may echo submitted evidence or request metadata. A synthetic smoke command requires an explicit live-call flag and makes exactly one call; automated tests never spend API credits.

Actual validation state: adapter request construction and credential-free operation are tested without network access. No live OpenAI or Anthropic request has been executed yet. Live readiness and comparative output quality must remain unclaimed until observed.

Never store hidden chain-of-thought. Retain structured results, useful analyst-facing rationale, provider/model/task/prompt version, timestamp, latency, token usage when available, and outcome.
