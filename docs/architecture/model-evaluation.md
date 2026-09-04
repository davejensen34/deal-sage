# Model evaluation contract

The Milestone 3.1 version-two contract evaluates evidence-bounded model observations without letting a model author facts, confidence, or workflow state. Its implementation is `app/research/model_evaluation.py`; the saved cohort in `tests/fixtures/milestone31_evaluation_v2.json` is fictional and safe for offline tests.

## Independent dimensions

Every completed result must classify seven dimensions independently:

1. `case_origin`: `signal_first`, `business_first`, or `hybrid`;
2. `identity_resolution`: `resolved`, `ambiguous`, `unresolved`, or `contradicted`;
3. `relationship`: current owner, former owner, successor, non-owner role, unclear, or none;
4. `relationship_time`: current at signal, ended before/at signal, began after signal, unclear, or not applicable;
5. `operating_status`: active, inactive, or unknown;
6. `contradiction_state`: none, resolved by timeline, or unresolved;
7. `research_disposition`: candidate supported, needs more research, no qualifying relationship, no business found, or conflict review.

This separation permits combinations that the version-one outcome enum could not express, such as a deceased former owner with a still-active business, or a resolved business-first subject whose successor remains unknown.

## Deterministic authority

The provider returns a schema-constrained observation, source citations, contradictions, unresolved questions, and a short summary. DealSage then:

- rejects citations not present in the supplied packet;
- checks relationship/effective-time compatibility;
- checks contradiction-state/detail agreement;
- applies safety-first disposition precedence: unresolved conflicts first, then unresolved/no-business outcomes, disqualifying relationship or inactive-business outcomes, fully resolved candidate support, and otherwise more research;
- compares each valid dimension with the pre-labeled fixture independently.

The disposition is an evaluation label, not a persisted analyst decision. No output changes confidence, identity, evidence, or case workflow state.

## Provider outcomes and metrics

Each provider path has exactly one execution outcome: `completed`, `incomplete`, `refusal`, `invalid`, or `failed`. Only internally consistent `completed` outputs enter dimension-level denominators. A truncation, refusal, invalid structure, provider error, or empty output therefore cannot be scored as a negative classification.

Input, output, and total tokens remain separate when the provider reports them. `AIExecution` also retains the split for normal application summaries while preserving total usage for compatibility. A failed call clears earlier usage before execution so one case cannot inherit another case's counters.

## Live-call gate

Automated tests use adapter mocks and never call a provider. The runner accepts only a version-two manifest and requires both `--confirm-live-calls` and an exact `--protocol-decision` value recorded in that manifest. The original seven-case cohort exhausted its approved call ceiling; this contract does not authorize a rerun or any new live cohort.
