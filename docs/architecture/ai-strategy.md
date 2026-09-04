# AI strategy

Use models only when they materially improve unstructured extraction, contextual interpretation, ambiguity analysis, evidence synthesis, or research planning. Deterministic code owns scoring arithmetic, validation, persistence, audit behavior, filtering, and state changes.

An `AIProvider` boundary defines extraction, summarization, and match-analysis capabilities. OpenAI and Anthropic adapters implement summarization; structured extraction intentionally raises `NotImplementedError`. Candidate evidence summary is optional, versioned, logged, evidence-bounded, and forbidden from changing confidence scores.

Actual validation state: provider imports are lazy and credential-free operation was tested. No live OpenAI or Anthropic request has been executed. Provider SDKs are optional dependencies and are not installed in the minimal Docker image, so the containerized AI path is not yet runnable even with credentials. This is tracked as technical debt, not represented as complete integration.

Never store hidden chain-of-thought. Retain structured results, useful analyst-facing rationale, provider/model/task/prompt version, timestamp, latency, token usage when available, and outcome.
