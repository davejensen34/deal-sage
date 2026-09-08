# Milestone 5 — Opportunity Intelligence Workflows

Status: proposed with narrowed scope; not active and awaiting explicit approval.

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

## Entry gate

Milestone 4 showed offline that model proposals can be reviewed and dispositioned without bypassing provenance, deterministic validation, or human authority. Its live run stopped at source reproduction before model analysis. Initial Milestone 5 work may therefore use existing reviewed evidence and deterministic state, but live model-derived enrichment, unattended refresh, and refresh-dependent alerts require a newly approved evaluation with retrieval-and-hash preflight for every frozen source.

## Boundary

Milestone 5 consumes the curated acquisition and reviewed-analysis paths established earlier. It does not create alternate ingestion, opaque scoring, or unreviewed model-to-opportunity automation.
