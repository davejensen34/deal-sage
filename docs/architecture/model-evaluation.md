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

## Broader transition review evaluation

Issue #130 adds the separate `m7-transition-evaluation-v1` contract in `app/research/transition_evaluation.py`. It tests the real review bridge against a hash-pinned, pre-normalized fictional cohort and does not call a model. `scripts/evaluate_milestone7_offline.py` uses disposable in-memory stores, ignores `.env`, and has no live mode. Precision, recall, fixture agreement, abstention and coverage carry explicit denominators; failures, missing dates/costs, actual human judgments and analyst time are separately reported. Passing this contract cannot set `live_precision_validated` or `source_coverage_validated` to true. See `docs/research/milestone7-evaluation.md` for the observed result and completed source-preflight results and remaining analysis approval boundary.

`analysis_preparation.py` prepares the separately proposed live observation cohort offline. Its CLI opens explicit SQLite input read-only, pins preflight bytes and checks artifact lineage, hashes and parser reproduction. Provider requests contain allowlisted source context only; agent expectations remain outside the request. State and private-company fit extend observation consistency without changing existing application promotion behavior. Output is an unapproved, hashable bundle, not executable authorization. Byte screening does not replace the future executor token gate.

`analysis_execution.py` consumes the separately approved, hash-pinned M7 bundle through a no-retry client. The CLI first reproduces it against read-only evidence, then claims execution once, persists reservations before network calls, counts full provider input before generation, and retains only validated observations or safe failure/usage metadata. Claim files survive failures and cannot be bypassed by changing the output filename. The first live precheck failed before generation; no model-quality conclusion follows. See the evaluation record for the original failure and retry boundary.

The separately approved `m7-analysis-execution-v2` run retained v1 history and used the same frozen requests. It produced one incomplete and two consistency-invalid responses. The generic consistency reason does not preserve the individual failed checks; safe per-check diagnostics and prompt/validator alignment need offline inspection before another live evaluation. No invalid response payload was retained or promoted.

### Offline observation contract v2

`observation_contract.py` separates schema-valid model observations from the deterministic research disposition. Its schema omits `research_disposition`; the evaluator derives that field with the existing precedence and target-fit guards, reuses semantic/citation checks, and checks case origin. It returns a copied observation plus the derived disposition, or safe diagnostics with no invalid payload. This is evaluation-only: no provider, database, score or promotion path. Existing frozen v1 requests and outcomes remain immutable.

`m7-observation-diagnostics-v1` codes are allowlisted before the existing executor persists consistency failures. Unsupported citation identifiers and unknown error text cannot enter those records. This improves future observability without reclassifying historical failures. The v2 prompt/schema is now integrated through `analysis_revision.py`: only the reviewed legacy bundle may be transformed, preserving source context and assessment date while replacing instructions/schema and the output cap. Preparation v2 freezes new request hashes. Execution v3 selects its own pinned bundle hash and persistent one-shot claim, validates observations with `assess_observation`, and persists `model_observation` separately from `deterministic_research_disposition`. The old execution v2 path remains unchanged. The revised bundle was explicitly approved and executed once under v3, with all three observations retained separately from code-derived dispositions. Its claim is consumed; no rerun is authorized. The executed limits were 20,000 input / 6,000 output tokens, a 90-second SDK timeout, zero retries and five cents per slot ($0.15 total). These are evaluation artifacts only; no application database or promotion state is changed.

Agent review of the retained v3 observations found temporal/geographic semantic limits beyond schema consistency: `active` does not encode the date supported by evidence, and an outside-state address does not establish absence of requested-state operations. Future offline contract clarification must preserve these distinctions without altering historical outputs or promotion guards. Contract validity remains separate from source truth and human usefulness.
