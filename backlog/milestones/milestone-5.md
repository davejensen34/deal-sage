# Milestone 5 — Opportunity Intelligence Workflows

Status: complete as of September 10, 2026. GitHub Milestone 5 tracks Issues #95–#100.

## Goal

Turn validated evidence and human-reviewed analysis into repeatable analyst workflows that surface explainable opportunities without weakening provenance.

## Intended scope

- Enrichment views that distinguish source facts, model inference, and analyst decisions.
- Saved research, dedicated watchlists, refresh workflows, and alerts.
- Explainable opportunity prioritization built from deterministic, versioned features.
- Coverage, freshness, cost, and analyst-disposition feedback loops.
- Export or integration seams that preserve evidence links and confidence boundaries.

## Likely sequence

1. Persist evidence-derived scoring features and reproduce all displayed scores deterministically.
2. Productize saved research and dedicated watchlists over reviewed cases.
3. Add bounded refresh workflows with visible source freshness and failure state.
4. Add opt-in alerts only after refresh behavior is trustworthy and cost-bounded.
5. Add export and integration seams that retain evidence references, inference status, and analyst disposition.

## GitHub workstreams

- #95 persisted reproducible candidate score provenance (complete).
- #96 productizes saved research and dedicated watchlists (implemented and validated in PR #102).
- #97 adds bounded source refresh workflows, subject to source preflight (implemented and live-validated in PR #103).
- #98 gates opt-in alerts on trustworthy refresh behavior (implemented and validated in PR #104).
- #99 adds provenance-preserving exports and integration seams (implemented and validated in PR #105).
- #100 reconciles documentation, validation, and closeout state (this closeout).

## Entry gate

Milestone 4.7 subsequently proved the full bridge over bounded real evidence: reproducible preflight, governed provider analysis, deterministic rejection, attributable disposition, and one conservative Utah review candidate. This satisfies entry for deterministic scoring provenance and reviewed-case analyst workflows. It does not establish autonomous opportunity-generation quality or sustainable source refresh. Live enrichment expansions, unattended refresh, and refresh-dependent alerts therefore remain separately gated by reproducible source preflight, measured analyst value, and bounded cost approval.

## Boundary

Milestone 5 consumes the curated acquisition and reviewed-analysis paths established earlier. It does not create alternate ingestion, opaque scoring, or unreviewed model-to-opportunity automation.

## Result

Milestone 5 delivered a coherent analyst workflow over the evidence and review foundations established earlier:

- Candidate scores now have immutable method/version, factors, supporting evidence IDs, calculation, and explicit legacy-demo or evidence-derived provenance.
- Analysts can save queue criteria and maintain identity-owned named watchlists without duplicating evidence.
- Colorado and Texas support explicitly initiated, 1–100 record, zero-cost source refreshes with durable attribution, contract fingerprints, acquisition linkage, safe failure state, and honest freshness limits. Utah remains delivery-based.
- Analysts can opt into in-app notifications for refresh failure and quarantine; successful refreshes stay quiet and subscriptions cannot initiate work.
- The authenticated candidate queue exports versioned JSON and CSV projections that preserve public evidence references, recorded relationship semantics, deterministic score provenance, freshness, and analyst disposition while excluding retained source content, analyst notes, model payloads, request metadata, and URL query parameters.

The milestone did not establish autonomous acquisition, comprehensive beneficial-ownership coverage, unattended refresh, external alert delivery, or generalized live-model quality. Those boundaries remain explicit gates rather than implied capabilities.

## Validation

At Issue #99 completion, all 179 backend/API tests and seven frontend tests passed. The production frontend built with its existing large-chunk warning; GitHub backend, frontend, and Compose checks passed. The rebuilt PostgreSQL/FastAPI/Nginx stack rendered the candidate export workflow and returned a bounded versioned Texas export with every content-exclusion flag false. Earlier workstreams separately exercised two approved five-record Colorado and Texas refreshes at $0. Milestone 5 made no live search or model calls and incurred $0 external spend.
