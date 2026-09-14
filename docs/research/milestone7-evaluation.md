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

The offline implementation and metrics are validated, and the approved source preflight and September 14 model run are complete. The model run did not yield a valid observation. Live precision, reproducible coverage and observed analyst value are not validated. Issue #130 and Milestone 7 stay open. Offline prompt/validator inspection and versioned integration are complete. The revised approved analysis is complete below. Next are human usefulness review and offline clarification of temporal and geographic observation semantics before any further live evaluation or scope closeout. This record does not silently waive those gates.

## September 14 approved model run

After automatic review rejected generic continuation as data-transfer authorization, Dave Jensen explicitly approved sending the three frozen public-source packets to OpenAI. Protocol `m7-analysis-execution-v2` used the unchanged bundle and model snapshot, with a separate execution claim and result file. The v1 claim and failed attempt were preserved. Source/request hashes were reverified before execution, SDK retries remained disabled, and the requests kept their frozen September 11 assessment date rather than silently changing the evaluation context.

| Slot | Counted/reported input tokens | Output tokens | Outcome | Estimated model cost |
| --- | ---: | ---: | --- | ---: |
| UT succession | 1,550 | 2,000 | Incomplete at the output limit | $0.0043875 |
| TX founder exit | 2,094 | 1,790 | Invalid: observation consistency | $0.0041035 |
| CO leadership change | 1,270 | 1,461 | Invalid: observation consistency | $0.0032395 |

Three input-count prechecks and three model-analysis requests ran. All input counts were below 20,000, and output usage remained within 2,000 per call. The returned model was `gpt-5-mini-2025-08-07` in all three calls. Reported usage totaled 4,914 input and 5,251 output tokens; estimated generation cost was **$0.0117305**, against **$0.15 reserved**. Actual invoiced spend remains unavailable. No search, evidence retrieval, model substitution, replacement request, case reopening or promotion occurred.

Zero of three observations passed the evaluation contract. One incomplete response and two invalid responses are execution outcomes, not three negative business findings or evidence of poor source quality. Precision and dimension agreement are unavailable with zero valid observations. The invalid responses were not persisted; the retained reason `observation_consistency` does not identify the individual failed checks. Consequently, this record cannot attribute either failure to ownership reasoning, target fit, citations or disposition precedence. No human usefulness or time-saved observation was collected.

The ignored result is `.local-validation/m7-preflight/analysis-results-v2.json`, with the permanent `.m7-analysis-execution-v2.claimed` marker beside it. Existing source packets remain available for offline inspection. Do not regenerate discarded responses through unapproved calls. Before another live experiment, inspect the frozen instructions against the deterministic contract and add safe per-check diagnostic codes without retaining invalid payloads. Treat the output cap as an observed constraint; changing it requires a newly bounded protocol, not an automatic retry.

All 295 backend/API tests passed on Windows. The nine execution-guard tests passed before this run. No UI changed. These engineering checks do not convert the failed live evaluation into a quality pass; Issue #130 and Milestone 7 remain open.

PR #137 initially failed the API container audit on 12 fixable high/critical Debian package findings (gzip, PCRE2, SQLite and Perl). The API Dockerfile now applies available distribution upgrades before app installation, matching the web image security-update convention. Scan thresholds remain unchanged; no waiver is used. Container and Compose CI validate the rebuilt runtime independently of model quality.

## Offline contract inspection — September 14

Issue #130 identified a reproducible prompt/validator mismatch: the frozen schema asks the model for `research_disposition`, while the validator requires an exact deterministic precedence that the prompt never specifies. A fictional executive-role observation labeled `needs_more_research` fails because code expects `no_qualifying_relationship`. That demonstrates a possible failure mechanism; the discarded historical responses are unavailable, so it does not establish why either live response failed.

`app/research/observation_contract.py` adds the separate, offline `m7-observation-v2` contract. Models describe evidence dimensions, citations, useful clues and uncertainty; the response schema excludes model-authored disposition. Code returns the original validated observation and a separately labeled deterministic research disposition. Unknown ownership and target fit do not erase a useful observation. Citation, relationship/timeline, contradiction and target-fit requirements still apply; an observation's derived disposition does not promote a candidate or change scores. Origin must match the supplied research context. Non-owner-role classification means the evidence establishes only that role, not that the person cannot own shares.

The existing executor now records versioned, allowlisted per-check codes for future consistency failures. Unsupported citation values are stripped; unknown error strings map to a fixed generic code. Invalid response bodies, schema details, and arbitrary error text remain excluded. A persistence-level mock test confirms these boundaries.

All 308 backend/API tests passed, including 13 new offline contract and diagnostic checks. They cover the reproduced disposition seam, useful unknown/non-owner observations, target fit, contradictions, citation and origin failures, response-schema rejection, mutation isolation and persisted diagnostic redaction. The frozen bundle still hashes to `5142f997f0f29192f8ca9bd4b47e68b4532ce3e611aa4d1bea5aceecfcaeb08e`; both historical execution claims remain present. No provider, source or search calls ran; spend was $0. No UI or application promotion policy changed.

The v2 contract is not connected to a live executor or the existing frozen request builder. A future integration must deliberately freeze new instructions/schema/requests and approval limits. The observed output-cap issue remains unresolved by this offline change. No claim is made that v2 improves live precision or cures the discarded responses. Issue #130 and Milestone 7 remain open pending the evaluation/closeout decision.

## Revised observation integration — September 14

Issue #130 now connects `m7-observation-v2` to preparation v2 and the separately gated `m7-analysis-execution-v3`. Source context, expectations outside the provider request, the September 11 assessment date and `gpt-5-mini-2025-08-07` remain unchanged. Only the model instructions/schema and output ceiling change. Preparation verifies the original reviewed bundle before transforming it; the historical bundle, claims and failed outcomes remain intact.

The revised ignored bundle is `.local-validation/m7-preflight/analysis-requests-v2.json`, SHA-256 `1e0ca8fd29c6d2016560bc81d9009cd429efdcafda8bfe5880baf2786b9fde3d`. Reproduce it without credentials or network calls from `apps/api`:

```powershell
.venv/Scripts/python.exe -m scripts.prepare_milestone7_analysis --manifest ../../.local-validation/m7-preflight/packets.json --database dealsage.db --evidence-dir data/evidence --observation-version v2 --output ../../.local-validation/m7-preflight/analysis-requests-v2.json
```

The proposed transfer is the same three frozen public-source packets (Savage succession, Aurora founder exit, Premier leadership) to OpenAI for three analysis calls. Each call has a provider input-count precheck, a 20,000-input-token ceiling, a revised 6,000-output-token ceiling, a 90-second SDK timeout, no retries, and a durable five-cent reservation; the total ceiling remains **$0.15**. At the reviewed [GPT-5 mini rates](https://developers.openai.com/api/docs/models/gpt-5-mini) of $0.25/M input and $2/M output tokens, the maximum generation estimate is $0.017 per call before cached-input savings. The larger output allowance addresses an observed constraint but does not guarantee completion or improved quality.

**Not authorized or executed:** the previous approval was exhausted by execution v2. Sending these revised requests requires new explicit user approval of the payload, destination and limits before supplying `--approved-protocol-id m7-analysis-execution-v3 --confirm-live-calls`. The CLI reproduces the selected frozen bundle against read-only local evidence before loading provider configuration. Execution v3 has its own permanent claim; it cannot rewrite or replay v1/v2 outcomes. Valid observations are retained under `model_observation`, with `deterministic_research_disposition` separately labeled. Invalid observations retain only safe diagnostics and usage metadata. Cases remain stopped and there is no automatic promotion.

All **315 backend/API tests passed** on Windows, including seven new offline integration checks. Mocked tests cover immutable bundle revision, unchanged evidence and expectation isolation, output limits, successful observation/disposition separation, one-shot behavior, legacy claim preservation, approval/hash/retry refusal before network activity, and rejection without persistence of model-authored disposition. Both local bundles reproduced byte-for-byte from retained evidence, and the execution-v3 claim was absent. No source, search or model calls ran; incremental external spend was $0. No UI changed. Live precision, analyst value and Milestone 7 closeout remain unvalidated.

## Approved observation-v2 execution — September 14

The user explicitly approved the named Savage/Aurora/Premier public-source packets to OpenAI after PR #139. Execution `m7-analysis-execution-v3` used the exact preparation-v2 bundle above, the original assessment date and model snapshot, three input-count prechecks and three analysis calls. All returned observations passed the v2 contract. No retries, substitutions, searches, acquisitions, case reopening or candidate promotions occurred. The $0.15 approval is now exhausted; it does not authorize another run.

| Packet | Input tokens | Output tokens | Contract result | Code-derived disposition | Estimated generation cost |
| --- | ---: | ---: | --- | --- | ---: |
| Savage succession (M7-UT-2) | 1,580 | 1,902 | Valid | no_qualifying_relationship | $0.004199 |
| Aurora founder exit (M7-TX-1) | 2,124 | 1,936 | Valid | no_qualifying_relationship | $0.004403 |
| Premier leadership (M7-CO-3) | 1,300 | 1,529 | Valid | no_qualifying_relationship | $0.003383 |

Reported usage totals **5,004 input and 5,367 output tokens**, with **$0.011985 estimated generation cost** and **$0.15 reserved**. Actual invoiced spend remains unavailable. These estimates use the previously reviewed rates, not an invoice. All calls returned `gpt-5-mini-2025-08-07`. Each completed within the proposed 6,000-output-token ceiling; all actually used fewer than 2,000 output tokens. This small rerun changed both prompt/schema and allowance, so it does not isolate which change helped or prove the larger ceiling was necessary.

The ignored immutable result is `.local-validation/m7-preflight/analysis-results-v3.json`, SHA-256 `906a5ba69502ad4edf5ba4291938a8de59d3e2537d882ca7712d6e6fd8375799`. The `.m7-analysis-execution-v3.claimed` marker is present alongside the retained v1/v2 claims. Do not delete any marker to repeat the experiment. Model observations, deterministic dispositions and the following agent review remain separate from human decisions. The model output was not imported into the application research database or presented as analyst acceptance.

### Agent review of retained observations

This is an offline comparison with the frozen source text and preflight expectations, not independent verification or human ground truth. All three observations retain useful narrative detail and follow-up questions even though none establishes a qualifying ownership relationship. `no_qualifying_relationship` applies to the evidence presented; it is not a finding that the executive owns no shares or that the business has no research value.

- **Savage:** preserves management succession, the self-description as privately held/family-owned, a source-reported 4,000-plus team members and the planned leadership dates. It does not infer executive ownership. The next useful checks are actual transition completion and ownership/control evidence; no audited revenue, profitability or acquisition attractiveness was established.
- **Aurora:** preserves the founder/executive departure and Texas operating clue while recognizing the source's publicly traded status. It distinguishes role exit from equity sale. The dates are announced effective dates, not independently confirmed completion; regulatory filings are referenced by the article but were not retrieved in this run.
- **Premier:** preserves the conditional CEO succession and North Carolina address. It does not equate the executive role with ownership. Colorado fit is unsupported by this packet; the output's stronger `out_of_scope` label is not proof that the company has no Colorado operations. Related-article headings are clues about the acquisition, not independently retrieved transaction evidence.

Two contract limitations remain visible despite a 3/3 valid-output rate. First, all three outputs say `operating_status=active`, although the source dates precede the frozen assessment date and the narratives ask for current confirmation. The enum does not carry a separate observation date; these outputs do not establish current operations as of September 11. Second, geographic fit lacks an explicit distinction between a supported requested-state operating connection, legal domicile, and absence of evidence. An outside-state address alone cannot prove absence of in-state operations. These findings warrant offline temporal/geographic contract clarification, with fictional regression fixtures, before stronger quality claims. Do not silently rewrite these retained outputs or loosen promotion guards.

### Measures and remaining decision

Execution/contract completion is **3/3**; failed, incomplete and invalid outcomes are **0/3** in this run. Useful summaries are retained for all three packets, but usefulness has only been assessed by this coding agent. Ownership-supported observations are **0/3**, actual promotions are **0**, and promotion precision has a zero denominator and remains unavailable. Frozen-context comparison supports the narrow role/ownership distinction and Aurora public-company exclusion; temporal/geographic concerns prevent treating overall dimension agreement as a quality pass. The prior v2 failed outcomes remain part of the record, not replaced by this run. No per-family or statewide precision estimate is justified by three selected packets spanning only three signal families.

Human usefulness, recorded analyst decisions and time saved remain **unmeasured**. Source sustainability, representative coverage, current ownership and recommendation attractiveness remain unvalidated. Next: review these three retained observations with a human analyst and clarify the temporal/geographic contract offline under Issue #130. No further external call is authorized by this record. Milestone 7 remains open.

Before the live run, all 17 execution/revision guard tests passed on Windows. This increment changes documentation only; the existing full 315-test and five-job CI validation belongs to PR #139. PR validation for this outcome record is recorded on its linked GitHub PR. No UI changed.

## Offline contextual review — September 14

Issue #130 adds an attributed deterministic assessment around the retained v3 observations. The original model observations and all three execution histories remain unchanged. Reviewer context is an explicit coding-agent interpretation with citations, not human acceptance or a new source fact. This is an offline evaluation feature, not an application UI or promotion-policy change.

From `apps/api` on Windows:

```powershell
.venv/Scripts/python.exe -m scripts.review_milestone7_observations --result ../../.local-validation/m7-preflight/analysis-results-v3.json --bundle ../../.local-validation/m7-preflight/analysis-requests-v2.json --output ../../.local-validation/m7-preflight/context-review-v1-final.json
```

The runner verifies both frozen input hashes and refuses to overwrite an existing report. Its ignored output hashes to `5adcab7fec45cc486afdea4c63830fbeb6bd30f1cd500bb00a041ba01f16c528`. It reads no credentials or database and has no provider/live mode.

| Packet | Agent-interpreted operating evidence date | Temporal scope at 2026-09-11 | Operating status at assessment | Requested-state operating relevance |
| --- | --- | --- | --- | --- |
| Savage | 2024-06-03 | Historical | Unknown | Unknown; Utah dateline alone is insufficient |
| Aurora | 2025-05-08 | Historical | Unknown | Supported by cited Texas operation |
| Premier | 2026-01-09 | Historical | Unknown | Unknown; NC address does not exclude CO |

All three original summaries, questions and labels survive alongside the contextual assessment. The `no_qualifying_relationship` guidance remains unchanged because the cited executive/founder roles do not establish ownership; no candidate was promoted. Historical evidence remains available to inform further research. No same-day freshness requirement is imposed on the application: this offline policy simply declines to extrapolate an assertion beyond its supported date without an explicit continuity policy. Geographic relevance refers to cited operating context and does not establish current operating coverage or legal domicile.

All **342 backend/API tests passed** on Windows. The 27 new fictional checks cover active and inactive historical/undated assertions, contemporaneous evidence, scoped operating presence/absence versus address/dateline/domicile, invalid/future dates, missing and unsupported citations, role precedence, input isolation, invalid model refusal and report hash binding. The frozen live report was reviewed offline, not rerun. External spend and provider/source/search calls were zero. No UI changed.

The temporal/geographic clarification is now implemented for offline review. Human usefulness, analyst time, representative precision and source sustainability remain unmeasured. Next work should use actual human feedback on the retained review before deciding application integration or another bounded evaluation; no further live run is authorized and Milestone 7 remains open.

## Analyst review surface — September 14

Issue #130 adds **Research → Review a retained evaluation package**, at `/research/evaluation`. The page separates retained source evidence, original model observations, deterministic contextual assessment, and the analyst's usefulness judgment. It loads only a file explicitly selected by the user, in the browser; it does not upload evidence, query providers, mutate cases or imply acceptance. External source links are optional user navigation, not an automatic part of review.

Create the real three-packet package from `apps/api`:

```powershell
.venv/Scripts/python.exe -m scripts.review_milestone7_observations --result ../../.local-validation/m7-preflight/analysis-results-v3.json --bundle ../../.local-validation/m7-preflight/analysis-requests-v2.json --format review-package --output ../../.local-validation/m7-preflight/analyst-review-package-v1.json
```

This ignored local package was generated successfully with SHA-256 `e76bb18c0d421a622c73fcdcbe1966957a3b2eb0047877aa7e4327cec3d54749`. Input and output files remain separate and the command refuses overwrite. No new live call is needed to inspect it. The default CLI format remains the prior context-only report.

Select the package on the review page, inspect source text against the model and contextual guidance, then explicitly choose useful for triage, not useful yet, or defer for each reviewed packet. Add a rationale and optionally the minutes actually spent reviewing. Enter your name and download feedback JSON. Unanswered packets remain unreviewed; blank duration stays unknown. The export binds the exact file fingerprint and is self-attributed human feedback, not an authenticated acceptance event. Retain the downloaded file with the package; it is not saved to the application database. A future metric import must verify the package binding before counting it. No time saved is inferred from review duration.

Validation: **343 backend/API tests and 19 frontend tests passed** on Windows. The production TypeScript/Vite build passed with its existing large-chunk warning. Windows lacked npm on PATH, so the installed Node runtime executed the same local TypeScript, Vitest and Vite entry points directly. The new backend regression verifies source/model/context separation, expectation exclusion and input hash refusal. Five frontend tests cover explicit/missing judgments, duration validation, exact-byte digest invocation, package/citation rejection, safe links, literal HTML-like source text, layer separation, failed-import reset and absence of API uploads. Rendered inspection used an isolated loopback Vite harness with fictional data at the available narrow viewport; source/model/context sections and test-only feedback export rendered correctly. That simulated export is not human usefulness evidence. The live application's web container was not redeployed in this increment.

No source, search or model calls occurred; incremental external spend was $0. Actual human feedback remains outstanding. Milestone 7 and Issue #130 remain open; this feature does not claim representative live precision or automatically close quality gates.

## Feedback validation and metrics — September 14

Issue #130 adds a credential-free importer/summarizer for the review page's `m7-human-usefulness-v1` downloads. It accepts only files explicitly supplied on the command line; it does not inspect or change the open browser, scan Downloads, or count a test export automatically. The exact retained review package is pinned. Hash validation and strict fields establish linkage and shape, not authenticated human authorship.

From `apps/api`, first export your actual judgments from the review page, then name that file explicitly:

```powershell
.venv/Scripts/python.exe -m scripts.summarize_milestone7_feedback --package ../../.local-validation/m7-preflight/analyst-review-package-v1.json --feedback '<absolute-path-to-your-export.json>' --output ../../.local-validation/m7-preflight/usefulness-summary-reviewed-v1.json
```

Repeat `--feedback` for additional deliberately selected exports. Overlapping reviewer/packet judgments are refused, including revisions and duplicate downloads, so choose which export should count. Original files remain unchanged. The output must be a new file; there is no overwrite option. Keep feedback files with the summary for audit by their retained hashes.

A no-feedback validation ran against the real package with no `--feedback` arguments, producing the ignored `.local-validation/m7-preflight/usefulness-summary-no-input-v1.json` (SHA-256 `ae7f98787946609ddd592cd18bfe6bd6aab1bcadc2ab72d42bd0a0c62c87a190`). It reports **0 judgments, 0/3 packet coverage, null usefulness and null known review duration**, with time saved, promotion precision and analyst acceptance also null. This describes the deliberately empty input set; it does not assert that no user export exists elsewhere. No actual human feedback was supplied to or counted by this run.

All **375 backend/API tests passed**, including 32 new fictional validation and aggregation checks. They exercise partial/multiple-reviewer denominators, defer in the usefulness denominator, zero versus missing duration, stable file fingerprints, Unicode/case/whitespace duplicate detection, disjoint partial exports, malformed/extra fields, hash mismatch, missing/duplicate/unknown slots, invalid times and timestamps, duplicate JSON keys, input limits, and CLI no-overwrite behavior. The fixture data remains test-only. No UI changed, so the existing rendered review page remains untouched; no frontend validation is claimed beyond its prior PR and current CI.

No source/search/model calls or external spend occurred, and no application database was read or written. Actual usefulness feedback, representative precision and source sustainability remain outstanding. Milestone 7 and Issue #130 stay open; metrics never close them automatically.
