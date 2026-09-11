# Milestone 6.1 — Discovery lead prioritization

Dave approved an additional Milestone 6 feature before Milestone 7 on September 11, 2026. The agent assigned the working label "Milestone 6.1"; that label was not a separately approved GitHub milestone. Milestone 6's completed operational closeout is preserved.

## Inspection and scope

ConfidenceService already weights source assertions by authority, directness, uncertainty, recency, and independence. It does not require every assertion to be verified. SearchService retains uncertain candidates, but the Research case narrative omitted them. The frontier could prioritize questions only after another caller created them. The six-slot exercise used operational scripts rather than this full loop, and produced no qualified opportunities; it did not establish that the retained clues were unusable.

Deliver an analyst-visible discovery layer: deterministic, explained research-priority points; source suggestions clearly attributed as unverified; query/evidence references; independent access status; specific next questions; audited selection into the existing bounded frontier. Scores are investigation heuristics, not calibrated probabilities. Repeated discoveries add no weight. Queuing performs no network calls, does not restart stopped cases, and never creates evidence, authoritative confidence, model acceptance, or candidate promotion.

## Acceptance

- Incomplete and blocked-source clues remain visible with a useful permissible next question.
- Priority rules are versioned and shown; selected priorities and lineage are snapshotted in audit history.
- Follow-up selection is role-protected and repeat submissions do not reset attempt budgets.
- Backend and rendered frontend verification cover discovery, repeat results, case boundaries and stopped cases.
- No new providers, paid experiments, expanded signal families, or Milestone 7 activation.

## Workflow and validation

Local implementation validated: 214 backend/API tests and 12 frontend tests passed; production frontend build passed with the existing large-chunk warning. The Windows evidence-storage assertion now compares Path objects rather than assuming POSIX separators. The live API returned liveness after restart, and rendered inspection of the retained Texas case showed all 13 discovery clues with priorities and disabled follow-up actions for the stopped case. No research/model calls were made during implementation. No schema migration is required.

GitHub Issue creation was attempted before implementation and denied with `403 Resource not accessible by integration`. Continuing implementation without resolving the Issue prerequisite was a workflow violation. Local commit `1dcc8a0` predates [Issue #126](https://github.com/davejensen34/deal-sage/issues/126), created retrospectively at Dave's explicit request after he installed the connector for this repository. The repair publishes the existing implementation on `codex/feat-126-discovery-leads` for PR review and CI; it does not claim the original Issue-first sequence occurred. The original local branch remains preserved. Publication/review must complete before Issue closure; Milestone 7 remains proposed.

Observed limitation: the current OpenAI search adapter supplies generic relevance and `other` source type for the retained cohort. Discovery-query context remains useful, but this heuristic cannot meaningfully rank business attractiveness or semantic relevance from metadata the adapter does not retain. Model-assisted clue enrichment and evidence-backed recommendation quality remain separate work, not implied by passing plumbing tests. Retrieval failures from the operational script are retained in its private report; application access approval alone does not prove successful retrieval.

## Publication and review record

[PR #127](https://github.com/davejensen34/deal-sage/pull/127) publishes the feature and corrected process record. The implementing agent's self-review checked authorization, same-case lineage, stopped-case refusal, serialized repeat selection, atomic audit/frontier persistence and absence of external dispatch or authoritative acceptance. This is not independent reviewer approval. GitHub Actions on the PR is the authoritative record for backend, frontend, Compose, dependency-audit and container-audit validation; merge remains conditional on all required checks succeeding. The Issue closes through the PR merge, never by retroactively asserting that the original workflow was followed.

## Deferred scope

This slice makes clues actionable within the planner; it does not deliver autonomous execution, proven recommendation precision, financial enrichment, or database-configurable acquisition limits. Those require separate bounded work. The generalized ResearchCase remains suitable for future use cases without weakening its evidence boundaries.
