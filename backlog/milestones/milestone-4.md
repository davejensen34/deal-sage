# Milestone 4 — Intelligent Business Discovery and Analysis

Status: in progress as of September 8, 2026; no new live model calls or spending are authorized.

## Goal

Productize evidence-bounded model assistance for business-detail extraction, identity and relationship ambiguity analysis, synthesis, and research planning while deterministic controls and human review remain authoritative.

## Entrance evidence

- Milestone 3 provides replayable, provenance-preserving bounded evidence from Colorado, Utah, and Texas.
- Milestone 3.1 provides provider-neutral OpenAI and Anthropic adapters, a bounded research frontier, traceable claims and inferences, analyst conclusions, and a version-two multidimensional evaluation contract.
- The version-one live cohort is negative evidence, not a quality claim. The version-two contract passes fictional offline fixtures but has not been evaluated live.

These foundations are adequate to begin productization. They are not authorization for unrestricted research, a new provider cohort, recurring cost, or automatic publication of model output.

## Sequenced workstreams

- 4.1 — Issue #69
- 4.2 — Issue #64
- 4.3 — Issue #63
- 4.4 — Issue #70
- 4.5 — Issue #71 (separately gated live evaluation)
- 4.6 — Issue #72

Progress: Issue #69 implements the 4.1 immutable proposal and execution-provenance contract with case-local lineage, safe structured output, explicit non-completed outcomes, and offline validation. Issue #64 productizes business extraction and identity/relationship ambiguity analysis over minimal case evidence packets, with deterministic citation, non-name, timeline, and explicit-owner-role checks.

### 4.1 — Durable model proposals and execution provenance

- Define one persisted proposal contract for extraction, match analysis, synthesis, and research-plan suggestions.
- Link every proposed observation to supplied case evidence or curated claim IDs.
- Retain task, provider, model, prompt/schema version, timestamp, latency, split token usage, bounded cost, and explicit execution outcome.
- Represent incomplete, refusal, invalid, and failed calls without converting them into research conclusions.
- Keep provider payloads, hidden reasoning, secrets, and unsafe error bodies out of persisted analyst records.

### 4.2 — Evidence-bounded extraction and ambiguity analysis

- Productize structured business-detail extraction through the existing provider boundary and deterministic validation layer.
- Add evidence-bounded person/business and relationship/timeline ambiguity analysis that can abstain and expose contradictions.
- Prevent unsupported citations, name-only resolution, registered-agent-to-owner promotion, and model-authored authoritative facts or scores.
- Preserve credential-free operation with deterministic fixtures and provider mocks.

### 4.3 — Bounded research-plan proposals

- Allow a model to propose a next question, source type, or research action using the existing `ResearchFrontierItem` and `ResearchStep` contracts.
- Require deterministic enforcement of source permissions, query/document/model/step/time/cost budgets, attempt limits, and stopping reasons before execution.
- Distinguish a proposed plan from an approved or executed action in persistence and the analyst narrative.

### 4.4 — Analyst review and disposition workflow

- Present source facts, DealSage/model inference, contradictions, gaps, and analyst decisions as distinct layers.
- Let an authenticated analyst accept, correct, reject, or defer a proposal with rationale and audit attribution.
- Make accepted corrections new human decisions linked to evidence; never rewrite the original provider output.
- Expose enough execution provenance and safe failure detail to assess trust without exposing raw private evidence.

### 4.5 — Governed version-two quality evaluation

- Freeze a human-labeled, evidence-safe cohort and protocol before any live calls.
- Obtain explicit approval for providers, models, case count, call ceiling, and total cost ceiling.
- Measure per-dimension quality, citation validity, abstention, contradiction handling, reproducibility where tested, latency, tokens, and cost.
- Record negative or partial results honestly and use them to decide whether Milestone 5 may consume reviewed model output.

### 4.6 — Reconciliation and milestone decision

- Run backend, frontend, migration, build, Compose, and rendered UI validation appropriate to the implemented changes.
- Reconcile the milestone file, related backlog items, roadmap, architecture, current state, and GitHub milestone before closeout.
- Record whether reviewed analysis is adequate for Milestone 5; do not start Milestone 5 automatically.

## Definition of done

- At least one real analyst workflow uses each productized capability selected from extraction, ambiguity analysis, synthesis, and planning; explicitly deferred capabilities are recorded rather than implied.
- Every model proposal is schema-validated, evidence-linked, provenance-complete, immutable as an execution result, and visibly non-authoritative until analyst disposition.
- Deterministic code rejects unsupported citations and contradictions, enforces all research and cost budgets, and owns persistence transitions and scores.
- Analysts can accept, correct, reject, or defer proposals with an attributable audit trail while original output remains intact.
- Disabled-provider and provider-failure paths leave the core application functional and do not manufacture facts or leak provider content.
- The approved version-two live evaluation is completed within its ceiling, or the milestone records an explicit decision to stop without claiming quality validation.
- Findings support an evidence-backed proceed/change/stop decision for Milestone 5.

## Explicit gates and boundaries

- Activating Milestone 4 requires a user-approved start, a GitHub milestone, and implementation-ready Issues derived from these workstreams.
- Workstreams 4.1 through 4.4 use mocks and fictional fixtures by default. They do not require live model spending.
- Workstream 4.5 requires a separate protocol and cost approval. Existing API keys are configuration, not spending authorization.
- Models cannot silently mutate source evidence, validated facts, identity decisions, workflow state, or deterministic confidence scores.
- Milestone 4 does not add autonomous crawling, recurring source purchases, opportunity scoring changes, alerts, enterprise infrastructure, or national coverage.
