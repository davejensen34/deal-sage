# Milestone 4 — Intelligent Business Discovery and Analysis

Status: complete with a change decision as of September 8, 2026.

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

Progress: Issues #69 and #64 complete 4.1–4.2 with durable model proposals, safe execution provenance, structured extraction, and evidence-bounded ambiguity analysis. Issue #63 completes the offline-validated 4.3 loop: schema-constrained next-action proposals, deterministic approval with durable frontier lineage, permissioned document retrieval, immutable artifact-first evidence landing, optional disabled-by-default OpenAI web discovery, audited one-step orchestration, duplicate suppression, bounded retries, and explicit terminal reasons. Issue #70 completes 4.4 with immutable, attributable analyst accept/correct/reject/defer records and an evidence-aware review surface that leaves provider output untouched. Issue #71 executed the approved protocol using three search calls and an estimated $0.06, then stopped before model analysis because none of the six frozen anchors reproduced as qualified evidence. The initial runner incorrectly continued discovery after the first failure; its fail-closed behavior is corrected and the protocol will not be rerun. Issue #72 reconciles and closes the milestone.

## Result and change decision

Milestone 4 completes the productized, provider-neutral proposal and analyst-review boundary. Fictional fixtures and mocks validate extraction, ambiguity analysis, research planning, deterministic approval, immutable provenance, and attributable disposition without requiring AI for core operation.

The live evaluation did not validate model quality. Its frozen source packet failed before model execution, demonstrating that reproducible source qualification—not additional prompting—is the immediate constraint. Milestone 5 may proceed only with workflows that consume existing reviewed evidence or deterministic state. Live model-derived enrichment, unattended refresh, alerts based on refreshed evidence, and claims of model quality remain gated by a newly approved evaluation whose preflight retrieves and hashes all evidence before the first paid call.

Closeout validation observed 151 backend/API tests and five frontend tests passing, a production frontend build, all sixteen migrations upgrading, downgrading, and re-upgrading on an empty SQLite database, valid Compose configuration, a rebuilt healthy PostgreSQL/FastAPI/Nginx stack, successful `/api/health`, and a rendered local dashboard. The build retains its existing large-chunk warning; no UI behavior changed in the closeout.

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

### 4.3 — Dynamic opportunity research loop

- Discover candidate evidence from interchangeable search providers without requiring a known person or business name; support signal-first, business-first, and hybrid case origins.
- Treat search results as untrusted source candidates. Permit retrieval only after deterministic URL-safety, source-access, case-budget, and attempt checks.
- Land retrieved documents with immutable provenance and content hashes before extraction or model use; search snippets and model statements are never source evidence.
- Let a model propose evidence-bounded extraction, ambiguity analysis, the next question, source type, query, or research action. A proposal must cite the supplied case evidence or claims and may abstain.
- Require deterministic approval before a proposed search or follow-up action enters the existing `ResearchFrontierItem` and `ResearchStep` execution path.
- Iterate only while new evidence or an unresolved material question justifies another step. Enforce query, document, model, step, attempt, elapsed-time, and cost ceilings plus explicit convergence and stopping reasons.
- Keep discovery, retrieval, model curation, approved execution, and analyst disposition distinct and auditable.

### 4.4 — Analyst review and disposition workflow

- Present source facts, DealSage/model inference, contradictions, gaps, and analyst decisions as distinct layers.
- Let an authenticated analyst accept, correct, reject, or defer a proposal with rationale and audit attribution.
- Make accepted corrections new human decisions linked to evidence; never rewrite the original provider output.
- Expose enough execution provenance and safe failure detail to assess trust without exposing raw private evidence.

### 4.5 — Governed end-to-end quality evaluation

- Freeze a human-labeled, evidence-safe cohort and protocol before any live calls.
- Obtain explicit approval for providers, models, case count, call ceiling, and total cost ceiling.
- Exercise dynamic discovery through reviewed opportunity output, rather than evaluating an isolated model prompt.
- Measure source yield and permission failures, retrieval and provenance integrity, per-dimension model quality, citation validity, abstention, contradiction handling, convergence, reproducibility where tested, latency, tokens, and cost.
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
- Workstreams 4.1 through 4.4 use mocks and fictional fixtures by default. Live-capable adapters may be implemented and tested without network access, but no provider calls or spending are implied.
- Workstream 4.5 requires a separate protocol and cost approval. Existing API keys are configuration, not spending authorization.
- Models cannot silently mutate source evidence, validated facts, identity decisions, workflow state, or deterministic confidence scores.
- Milestone 4 does not add autonomous crawling, recurring source purchases, opportunity scoring changes, alerts, enterprise infrastructure, or national coverage.
