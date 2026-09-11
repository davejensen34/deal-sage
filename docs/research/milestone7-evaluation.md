# Milestone 7 comparative evaluation

Issue #130. Status: offline contract validated; live precision, source sustainability and analyst value remain unvalidated. Milestone 7 remains active pending the live-evaluation or scope-closeout decision. No later milestone is activated.

## What was run

From `apps/api` on Windows:

```powershell
.venv/Scripts/python.exe scripts/evaluate_milestone7_offline.py --output ../../.local-validation/milestone7-evaluation.json
.venv/Scripts/python.exe -m pytest -q
```

The runner has no live mode or database-selection argument. It bypasses `.env`, disables search/model providers, and builds a disposable in-memory database for each fixture. It executes the actual evidence, claim, simulated proposal/disposition, and review-promotion services. It does not run discovery, extraction or a model. Nothing enters the existing research corpus.

The frozen cohort is `apps/api/tests/fixtures/milestone7_transition_cohort_v1.json`. Its normalized JSON SHA-256 is `5a031b823aa84c022471c0b97929f47438c0c3227a31ab1ad65d1f62d1d6663f`; the runner rejects changed cases or labels until the version/hash is deliberately reviewed. Normalization makes the fingerprint stable across Windows and Unix line endings.

Each of eight signal families has eight independently pre-labeled scenarios: supported, unknown event date, executive role, registered-agent role, name-only identity, different business, open contradiction and cancelled event. The first two are eligible for human review; the remaining six stay in research. Text and normalized claims are fictional. The fixture acceptance is simulated input to the bridge, never a human usefulness observation.

## Observed outcome

| Signal family | Slots | Promoted / expected positive | Abstained | Promotion precision | Fixture agreement |
| --- | ---: | ---: | ---: | ---: | ---: |
| Possible death | 8 | 2 / 2 | 6 | 2 / 2 | 8 / 8 |
| Retirement | 8 | 2 / 2 | 6 | 2 / 2 | 8 / 8 |
| Succession | 8 | 2 / 2 | 6 | 2 / 2 | 8 / 8 |
| Ownership transfer | 8 | 2 / 2 | 6 | 2 / 2 | 8 / 8 |
| Founder exit | 8 | 2 / 2 | 6 | 2 / 2 | 8 / 8 |
| Dissolution | 8 | 2 / 2 | 6 | 2 / 2 | 8 / 8 |
| Restructuring | 8 | 2 / 2 | 6 | 2 / 2 | 8 / 8 |
| Leadership change | 8 | 2 / 2 | 6 | 2 / 2 | 8 / 8 |

All 64 executions completed: 16 review candidates, 48 abstentions, zero execution failures. Fixture promotion coverage was 16/64 (25%); abstention was 48/64 (75%). Event dates were present in 56/64 records. The fixture publication-to-retrieval interval was ten days in all 64 records. External cost was $0. Actual human usefulness, analyst time saved, source-population coverage and live timeliness were not measured.

All 272 backend/API tests passed. Tests include arithmetic with false positives/false negatives/failures, missing costs and dates, empty denominators, duplicate slots, forbidden network access, cohort drift and Windows line endings. Replacing promotion with an always-promote stub fails the evaluation gate (16/64 precision). No UI changed in this increment; UI validation belongs to PR #132.

## Meaning of the measures

- Promotion precision = expected-positive promotions / all promotions. This tests eligibility for human review, not truth of ownership or opportunity attractiveness.
- Positive recall = expected-positive promotions / expected positives among completed evaluations. Failures are reported separately, and any failure fails the offline gate.
- Fixture agreement compares the actual promotion/abstention with the pre-label among completed executions. Every case must agree for the offline gate to pass.
- Promotion coverage and abstention use all cohort slots, including failed slots in the denominator. They are not source-population coverage.
- Publication age is reported only for known dates. Unknowns are counted, never replaced with zero. Fixture age is not measured live acquisition latency.
- Costs retain measured/missing counts and an explicitly partial known total. Missing cost is not free execution.
- Human dispositions and usefulness are separate observations; usefulness uses all recorded human judgments, including defer. Missing human review and time remain unavailable rather than inferred from a simulated acceptance.

The small, constructed cohort validates engineering behavior. It is neither a representative sample nor calibrated live precision. Prior negative live results and deferred Issue #92 remain unchanged.

## Proposed source preflight — approval required

Protocol ID: `m7-source-preflight-v1`. This is a proposal, not approval or an executable unattended job. Approval would authorize only the following initial discovery/preflight envelope, not model analysis or candidate promotion.

| Slot | State | Signal | Origin | Initial query |
| --- | --- | --- | --- | --- |
| M7-CO-1 | CO | Possible death | signal_first | Colorado business owner obituary company |
| M7-UT-1 | UT | Retirement | signal_first | Utah business owner retirement |
| M7-UT-2 | UT | Succession | hybrid | Utah family business succession announcement |
| M7-CO-2 | CO | Ownership transfer | hybrid | Colorado privately held business ownership transfer |
| M7-TX-1 | TX | Founder exit | signal_first | Texas company founder departure |
| M7-UT-3 | UT | Dissolution | business_first | Utah business dissolution public notice |
| M7-TX-2 | TX | Restructuring | business_first | Texas private company restructuring announcement |
| M7-CO-3 | CO | Leadership change | signal_first | Colorado private company leadership change |

Ceilings: eight slots, at most two OpenAI web-search requests per slot (16 total), at most five results per request, at most three permitted page retrievals per slot (24 total), and at most two bounded official registry requests total (25 records each, Colorado/Texas only). Utah lookup uses the already retained BEL delivery; no new purchase. Every retry counts. At most $0.25 per slot and $2 total, including search-associated model/token charges; stop before a request whose conservative maximum could exceed either ceiling. No separate extraction/analysis model calls, automatic refresh, or external messages. Existing research budgets must be set and costs recorded before execution; missing price bounds block execution rather than imply zero cost.

For each slot, preserve the query and ranked results, including misses. Inspect candidates in returned order; do not replace an unsuccessful slot with a handpicked success. A second query may refine one retained clue and must record its rationale. Select the first permitted relevant source packet, keeping unresolved identity explicit. No known business name is required for initial discovery; business-first lookup begins only when discovery yields a business clue. This small state allocation does not support state-level or family-level statistical generalization.

Before retrieving any page, apply existing source-access checks. Use only permitted public business pages, notices, registries, and public profiles; do not bypass logins, access blocks, publisher restrictions or rate limits. Retain source URLs, publisher, publication/retrieval dates, selected excerpts, content hashes and parser lineage. Confirm retained bytes and excerpts reproduce. Mark absent, restricted, conflicting and stale evidence explicitly. A social or executive profile is corroboration, never proof of ownership.

Stop when the ceilings are reached, a cost cannot be bounded, access restrictions prevent retrieval, or the slot is exhausted. Do not initiate replacement experiments or rerun Issue #92. Report the source-preflight outcomes and actual spend even if no useful packet is found.

Only after preflight: freeze exact packets, expected assessment dimensions, proposed provider/model versions, token/call/cost ceilings and a fresh approval identifier before any model-analysis evaluation. That second phase requires separate approval. Record each human disposition and measured analyst time; do not infer trust or usefulness from a model score. A representative precision claim requires a larger approved sampling design beyond these eight exploratory slots.

## Milestone decision still needed

The offline implementation and metrics are validated. Live precision, reproducible coverage and observed analyst value are not. Issue #130 and Milestone 7 stay open until the user approves the next bounded evaluation or explicitly accepts an offline-foundation closeout with these limitations. This record does not silently waive those gates.
