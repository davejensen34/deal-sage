# Milestone 5 — Opportunity Intelligence Workflows

Status: active as of September 10, 2026. GitHub Milestone 5 tracks Issues #95–#100; Issue #95 is the first implementation workstream.

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
- #99 adds provenance-preserving exports and integration seams.
- #100 reconciles documentation, validation, and closeout state.

## Entry gate

Milestone 4.7 subsequently proved the full bridge over bounded real evidence: reproducible preflight, governed provider analysis, deterministic rejection, attributable disposition, and one conservative Utah review candidate. This satisfies entry for deterministic scoring provenance and reviewed-case analyst workflows. It does not establish autonomous opportunity-generation quality or sustainable source refresh. Live enrichment expansions, unattended refresh, and refresh-dependent alerts therefore remain separately gated by reproducible source preflight, measured analyst value, and bounded cost approval.

## Boundary

Milestone 5 consumes the curated acquisition and reviewed-analysis paths established earlier. It does not create alternate ingestion, opaque scoring, or unreviewed model-to-opportunity automation.
