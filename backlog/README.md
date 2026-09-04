# Product backlog

This directory preserves roadmap sequencing, milestone outcomes, product risks, and work not yet ready for execution. GitHub Issues are the actionable engineering record; repository backlog files preserve the durable product context that should survive individual Issues and pull requests.

Status vocabulary: `proposed`, `ready`, `in_progress`, `blocked`, `implemented`, `validated`, `deferred`.

Priority order is research correctness and provenance; owner-discovery and identity-resolution viability; analyst trust and workflow value; acquisition coverage, reliability, and cost; then advanced AI, scale, and enterprise concerns.

## Current product position

- Milestone 2.2 — Live Local Google Authentication is complete and validated.
- Milestone 3 — Multi-State Data Acquisition and Curation is active. GitHub Milestone 3 and Issue #20 opened the source-registry research slice; later implementation must remain tied to scoped Issues.
- `docs/project/current-state.md` is the detailed implementation and validation handoff.

## Approved forward sequence

1. Milestone 3 builds curated, replayable, multi-source data acquisition for Colorado, Utah, and Texas.
2. Milestone 4 adds provider-neutral OpenAI/Anthropic discovery and analysis over that curated evidence.
3. Milestone 5 turns reviewed evidence and analysis into ongoing opportunity workflows.

This ordering is a product constraint: model-assisted discovery must consume traceable curated evidence, and opportunity workflows must consume validated outputs. Neither may create a parallel path that bypasses provenance, deterministic validation, or human review.

## Source-of-truth contract

- `docs/product/roadmap.md` owns milestone sequence and product-level outcomes.
- `backlog/milestones/` owns durable milestone scope, definition of done, result, and validation status.
- `backlog/items/` owns proposed or deferred work that is not yet implementation-ready.
- GitHub milestones group approved execution work; GitHub Issues define actionable tasks; pull requests provide implementation and validation evidence.
- `docs/project/current-state.md` records what actually works, what is partial, and what remains missing.

When these records disagree, do not silently choose the most optimistic account. Inspect the implementation and validation evidence, correct the repository record in the active pull request, and reconcile GitHub state.

## Milestone lifecycle

When starting an approved milestone:

1. Create or update its `backlog/milestones/` file with goal, scope, definition of done, and `in_progress` status.
2. Create the corresponding GitHub milestone and implementation-ready Issues only for approved work.
3. Update this file and `docs/project/current-state.md` to name the active milestone.

Before closing a milestone:

1. Validate the implementation and record only evidence that was actually observed.
2. Update the milestone file with its result and final status.
3. Reconcile related `backlog/items/`, the product roadmap, and architecture or decision records when scope or knowledge changed.
4. Update this file and `docs/project/current-state.md` with the next approved state; use “no active milestone” when the next milestone has not been authorized.
5. Ensure the closing pull request links its GitHub Issue and includes the documentation changes, then close the GitHub milestone only after the pull request passes validation and merges.

CI can validate repository contents, but it cannot prove that narrative product status and GitHub milestone state are semantically aligned. The engineer or agent closing the milestone owns that reconciliation.
