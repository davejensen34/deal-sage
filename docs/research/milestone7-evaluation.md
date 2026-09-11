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

## Approved source preflight — September 11, 2026

Protocol ID: `m7-source-preflight-v1`. Dave Jensen explicitly approved this source-preflight envelope in the current development conversation after PR #133. Approval covers only the following initial discovery/preflight envelope, not model analysis or candidate promotion.

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

## Source-preflight outcome — September 11, 2026

The approved run stopped after 11 successful web-search requests and 11 HTTP requests, including six robots checks and five page requests. Four pages landed with matching stored SHA-256 hashes and reproducible local text extraction. One was subsequently excluded for an unresolved publisher-access contract. Three packets remain eligible for consideration in a separately approved analysis phase; this is not three qualified opportunities. No registry requests, Utah BEL lookup, separate model-analysis calls, candidate promotions or external messages occurred. All eight research cases were stopped and the local runner was closed against further calls.

| Slot | Searches | HTTP requests | Observed result and remaining uncertainty |
| --- | ---: | ---: | --- |
| CO possible death | 1 | 2 | A publisher-hosted obituary landed, but its retained content identified a Legacy-powered page. The hostname-only exclusion missed that publisher relationship. Excluded from further evaluation pending access review; no replacement search or analysis. |
| UT retirement | 2 | 2 | Initial results focused on retirement benefits. One publisher refinement found an executive retirement clue; retrieval failed the capability-field content guard. The clue remains useful discovery metadata, not verified ownership evidence. |
| UT succession | 2 | 2 | A company announcement describes CEO retirement and succession at a privately held family business. It reports over 4,000 team members, a useful size clue, but not audited fit. Named executives are not established owners. The June 2024 announcement is old; follow-up discovery found later leadership sources but they were not retrieved. |
| CO ownership transfer | 1 | 0 | Statutes, filing forms and regulatory guidance; no specific business transaction established. |
| TX founder exit | 1 | 2 | A reported founder/executive departure is a real transition clue, but the retained article explicitly describes a publicly traded company. Texas operations do not establish a local private-business target. |
| UT dissolution | 2 | 0 | Statutes and a public-notice portal remained non-entity results after one refinement. Administrative login was not accessed. |
| TX restructuring | 1 | 1 | Company announcement discovered; robots disallowed retrieval. No content retained and no access workaround attempted. |
| CO leadership change | 1 | 2 | A company announcement describes a conditional CEO transition and lists a North Carolina address. Colorado fit is not established; neither executive ownership nor completion of the transition is proven. |

The three refinements were limited to retained clues: a Utah publisher for an owner-retirement announcement, the Utah public-notice portal for a named dissolution, and the succession company's later leadership status. Queries, returned ranks, skip rationales, access failures and packet references are retained locally. Unused request allowances were not spent to fill the quota or replace misses. No official registry request was justified for the retained unresolved/out-of-fit packets; absence of a lookup is not a negative registry finding.

Search-associated provider usage estimates total **$0.153653**. Conservative reservations totaled **$1.32**, with at most $0.24 reserved in any slot, beneath the $2 / $0.25 ceilings. Reservations were persisted before each request and never released. The returned search model was `gpt-5-mini-2025-08-07`; each request disabled SDK retries and bounded tool calls and output. Estimates use reported input/output tokens and one web-search fee per request at the [model rates](https://developers.openai.com/api/docs/models/gpt-5-mini) and [tool pricing](https://developers.openai.com/api/docs/pricing) checked September 11. Actual invoiced spend is unavailable; reservations and estimates are not billing statements.

The ignored Windows packet record is `.local-validation/m7-preflight/packets.json`, SHA-256 `ae00203633d2f5e7bcf35c9160d44da814ea0f0f6949b79e9ac0296ad3032eb9`. It references exact raw-artifact and extracted-text hashes, case/evidence lineage, observed publication/event dates, retrieval timestamps, parser version and separately labeled agent interpretations. Raw pages, local database IDs, personal source details and credentials are not published in this repository. This Windows corpus remains separate from the historical Mac corpus.

Two acquisition limitations remain explicit under #130: hostname matching alone did not identify a white-label publisher, and robots response bytes were not retained, so those access decisions cannot be fully replayed offline. The retirement page also demonstrates that a whole-response capability-field rejection can prevent use of otherwise useful article content. These are access/sanitation gaps, not reasons to label the discovered business clues false. Source-policy review and safe extraction need a separate implementation decision before another acquisition run.

## Proposed next analysis envelope — not authorized

Use only the three frozen eligible packets above, retaining the public-company and geographic mismatch cases as negative controls. Suggested scope: one evidence-bounded evaluation per packet using OpenAI `gpt-5-mini-2025-08-07`, three calls total, no tools/search/retrieval, no retries, at most 20,000 input tokens and 2,000 output tokens per call, at most $0.05 per packet / $0.15 total reserved before execution. Fail before a call if its full serialized input cannot fit the bounds. No automatic promotion or authoritative score changes.

The expected dimensions are origin, entity identity, relationship semantics, relationship timing, operating status, contradictions and research disposition, plus explicit state/private-business fit and source age. Agent preflight expectations are separate from source assertions and are not human usefulness labels: the succession packet supports management succession but leaves ownership unresolved; the founder-exit packet fails private-company fit; the leadership packet does not establish Colorado fit. Models should extract useful clues and missing corroboration while retaining these limits. Ownership, financial attractiveness and present operating status must not be invented. The exact serialized requests, versioned evaluation contract and fresh approval identifier still must be frozen before execution. Human disposition and time measurement remain separate later observations.

## Offline analysis preparation — September 11, 2026

Issue #130 adds `scripts/prepare_milestone7_analysis.py`. It has no credentials, network client, live mode or database mutation path. It opens SQLite read-only, verifies case/evidence/artifact lineage and byte counts against the pinned preflight manifest, checks raw and extracted-text hashes, and reproduces the original parser. It refuses excluded, duplicate or substituted packets, escaped file paths, oversized requests and output overwrites. The existing parser is reproduced for integrity; this does not resolve its acquisition limitations.

From `apps/api` on Windows:

```powershell
.venv/Scripts/python.exe scripts/prepare_milestone7_analysis.py --manifest ../../.local-validation/m7-preflight/packets.json --database dealsage.db --evidence-dir data/evidence --output ../../.local-validation/m7-preflight/analysis-requests-v1.json
```

This command prepared three requests without modifying the corpus. The ignored bundle SHA-256 is `5142f997f0f29192f8ca9bd4b47e68b4532ce3e611aa4d1bea5aceecfcaeb08e`. It freezes the model, instructions, source inputs, structured-output schema, individual request hashes and proposed limits. Agent expectations remain outside each provider request. Publication age is computed offline from explicitly observed dates; missing dates stay missing. The observation contract extends the existing seven dimensions with independent state/private-company fit. Candidate-supported observations require both fits supported; uncertainty keeps an otherwise eligible observation in research. This validator does not change application promotion or claim policy.

All 286 backend/API tests passed, including nine preparation tests for offline operation, answer isolation, hash drift, excluded/duplicate packets, size bounds, path containment, target-fit consistency and read-only database lineage. No UI changed; no research, search or model calls were made, and external spend was $0.

The bundle is explicitly `not_authorized`. Its 16,000-byte serialized-request screen is conservative preparation, not measured provider token usage. A separately approved executor must check the full request against the 20,000 input-token ceiling, reserve cost durably before calls, disable retries, enforce single execution and reverify the bundle hash. It must preserve refusal/incomplete/invalid/failure outcomes and model/usage provenance. The [official model page](https://developers.openai.com/api/docs/models/gpt-5-mini) lists the requested snapshot and structured-output support, but marks the snapshot deprecated; account availability has not been tested. Do not silently substitute another model. No live executor is added by this increment.

## Approved execution attempt — September 11, 2026

The user's continuation directly following the three-call/$0.15 approval question approved the frozen bundle under `m7-analysis-execution-v1`. The source and request hashes were reverified through read-only SQLite before execution. `python -m scripts.run_milestone7_analysis` supplies the explicit bundle, manifest, database, evidence directory, environment file and output paths, plus `--approved-protocol-id m7-analysis-execution-v1 --confirm-live-calls`. The initial direct script invocation failed on a Python module import before network activity; module invocation resolved it.

The one-shot executor durably reserves five cents before each attempt, disables SDK retries, checks the complete input through the [provider token-count endpoint](https://developers.openai.com/api/reference/python/resources/responses/subresources/input_tokens/methods/count), enforces 20,000 input / 2,000 output tokens, and submits only the frozen requests. A persistent marker beside the bundle prevents rerunning with another output filename. Failures retain reservations. Only schema-valid, consistent observations are retained; refusal, incomplete, invalid and failed outcomes remain distinct, with safe usage/error metadata. There is no database mutation or automatic promotion.

**Observed result:** one input-count request was attempted, then a `ValueError` stopped execution before generation. Zero analysis calls, searches, source retrievals or promotions ran. One five-cent reservation remains; no generation usage was reported, and actual invoiced spend is unknown. No replacement request or model substitution was attempted. The original record captures the failure class but does not distinguish a missing/invalid count from an out-of-range count; it is not evidence that the provider or model is unavailable. New offline checks add safe reason codes for future approved runs, without rewriting this historical failure.

The ignored result is `.local-validation/m7-preflight/analysis-results-v1.json`; its persistent claim is `.m7-analysis-execution-v1.claimed` in the same directory. Do not delete that claim to rerun the experiment. All 295 backend/API tests passed, including nine executor checks covering one-shot behavior, failure reservations, token limits, approval refusal, valid/invalid observations, incomplete/refusal usage and safe count diagnostics. Existing research cases remain stopped. No model observation or human usefulness result was produced. Offline diagnosis reproduced a local SDK parsing defect: `cast_to=dict` raises `ValueError` even for a valid count response. The executor now uses `dict[str, object]`, verified through the real SDK with an offline HTTP transport. No additional live call was used to diagnose or validate this fix. A further attempt needs a separately recorded decision; the existing bundle and failure record remain unchanged.

## Milestone decision still needed

The offline implementation and metrics are validated, and the approved source preflight is complete. Live precision, reproducible coverage and observed analyst value are not validated. Issue #130 and Milestone 7 stay open; a further analysis attempt, acquisition fixes or a scope-closeout decision require explicit direction. This record does not silently waive those gates.
