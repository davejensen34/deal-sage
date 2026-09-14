# Recent-signal intake before paid analysis

Status: implemented. GitHub: [#144](https://github.com/davejensen34/deal-sage/issues/144). Milestone 7.

The first increment persists an opt-in case policy and implements cited deterministic freshness routing, dated discovery, narrative counts, lead-priority factors, and gates before analysis-step reservation and model execution. It preserves old/undated evidence as research material and keeps freshness separate from ownership confidence. See [the contract](../../docs/architecture/signal-intake.md).

The second increment connects the shared freshness routing to preparation v3 and execution v4. Read-only freezing verifies retained artifact/access lineage and captures all same-case transition assertions and conflicts. Execution regenerates requests, routes and budget limits before any reservation or token/model call, and the CLI rechecks current lineage before loading credentials. Empty/stale cohorts remain exclusion reports with zero spend; no fallback packets fill slots. Old bundle contracts and retained artifact hashes remain unchanged.

Case creation exposes configuration through the Python service, not an operator UI. A future recent cohort still requires reviewed source/date claims, a concrete request freeze and separate transfer/budget approval. Human feedback in #130 remains 0/3 useful; #145 tracks business-focused presentation. No new live evaluation is authorized. These product-value tasks remain open after the intake implementation.
