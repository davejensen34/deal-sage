# DealSage documentation

This directory contains living product and engineering specifications plus historical decision and validation records. When a historical record differs from the running product, [`project/current-state.md`](project/current-state.md) and the implementation are authoritative; correct the living record rather than rewriting an accurate historical observation.

## Start here

- [`product/vision.md`](product/vision.md) — product purpose and success definition.
- [`project/current-state.md`](project/current-state.md) — what is validated, partial, deferred, and next.
- [`product/roadmap.md`](product/roadmap.md) — milestone sequence and product outcomes.
- [`architecture/architecture.md`](architecture/architecture.md) — implemented system boundaries and extension points.
- [`governance/responsible-research.md`](governance/responsible-research.md) — mandatory data, evidence, privacy, and human-review rules.

## By purpose

- `product/` defines the vision, users, principles, and roadmap.
- `architecture/` defines current technical contracts for data, confidence, AI, evidence landing, and deployment.
- `deployment/` contains operator setup that supplements the root README.
- `governance/` contains rules that apply to every source, model, and analyst workflow.
- `research/` records source assessments, experiments, protocols, and observed results. These are dated evidence records, not blanket permission to collect from a source.
- `decisions/` contains immutable architecture decision records (ADRs). Supersede an ADR with a new decision; do not silently make an old decision read as though it were made later.

The durable backlog is in [`../backlog/README.md`](../backlog/README.md). GitHub Issues are the implementation-ready work record; backlog files preserve longer-lived context and milestone outcomes.

## Status language

Use `proposed`, `ready`, `in_progress`, `blocked`, `implemented`, `validated`, `deferred`, or `rejected`. “Implemented” means code exists. “Validated” requires recorded observed evidence. “Ready” permits only the bounded activity described in the record; it is not permission for unrestricted crawling, purchasing, or production use.
