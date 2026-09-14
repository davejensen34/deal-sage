# Milestone 7 recent discovery proposal

Issue [#130](https://github.com/davejensen34/deal-sage/issues/130). Protocol `m7-recent-discovery-v1`. **Approved and attempted September 14; stopped on the first query. Approval exhausted.**

The first real cohort was 0/3 useful because its signals were old and its presentation did not provide enough business value. Freshness intake (#144) and business briefs (#145) are now implemented. This next stage seeks new discovery candidates; it cannot establish source truth, ownership, size, actionable fit or human usefulness from search results.

## Reviewable outbound scope

Send eight fixed, name-free public-web research questions to OpenAI's existing `gpt-5-mini-2025-08-07` search integration. No local evidence, Utah files, retained packets, private business list, analyst feedback or corpus is included. All slots begin signal-first; a business need not be known beforehand. Later case enrichment can follow concrete business clues.

The proposed frozen assessment is **2026-09-14**, with a **90-day inclusive event window, 2026-06-16 through 2026-09-14**. Every submitted query below appends exactly `after:2026-06-15 before:2026-09-15`, using the shared application's date-hint function. Search engines may ignore those hints. Source-cited event/announcement review, not the search date or snippet, will determine eligibility later. Accepting this proposal would select this evaluation window, not change a production default.

| Slot | Signal | Query before the common date suffix |
| --- | --- | --- |
| CO-mortality | Possible death | Colorado business owner obituary company |
| UT-retirement | Retirement | Utah business owner retirement announcement |
| UT-succession | Succession | Utah family business succession announcement |
| CO-transfer | Ownership change | Colorado privately held business ownership transfer |
| TX-founder | Founder exit | Texas private company founder departure |
| UT-dissolution | Dissolution | Utah business dissolution public notice |
| TX-restructuring | Restructuring | Texas private company restructuring announcement |
| CO-leadership | Leadership change | Colorado private company leadership change |

One provider request per slot; at most one web-search tool invocation and 1,000 output tokens per request, five retained consulted-source references per slot, 40 references total before cross-slot deduplication, 45-second timeout and zero retries. No query refinements or replacement slots. SDK response storage is disabled. Any provider/contract/usage failure stops remaining calls; empty completed searches remain empty and do not cause extra calls. No model substitution if the pinned model is unavailable.

**Spending ceiling: $1 total.** Reserve $0.12 before each request, at most $0.96 for eight calls. At the [checked GPT-5 Mini rates](https://developers.openai.com/api/docs/models/gpt-5-mini) and [web-search pricing](https://developers.openai.com/api/docs/pricing), the conservative per-call allowance covers 400,000 input tokens at $0.25/M, 1,000 output tokens at $2/M, and one $0.01 tool call, rounded upward. Pricing was checked September 14. Reservations and reported-usage estimates are distinct from actual invoiced cost, which remains unavailable. Unexpected usage/model/tool-count results stop further calls. Both the assessment and pricing check expire after seven days; execution after September 21 requires renewed preparation/review.

## Prepared artifact and commands

The exact ignored bundle is `.local-validation/m7-recent-discovery/discovery-requests-v1.json`.

SHA-256: `838a49f7f1b79f604b3913f5445bd3b1ed76e3a0505df282728bd6ab7388c62f`.

The preparation command runs without credentials, network or database access. From `apps/api`, choose an unused output path:

```powershell
.venv/Scripts/python.exe -m scripts.recent_milestone7_discovery prepare --assessment-date 2026-09-14 --output ../../.local-validation/m7-recent-discovery/discovery-requests-v1.json
```

Only after the user approves the named transfer, window and budget, the run subcommand accepts `--bundle`, `--env-file`, `--approved-protocol-id m7-recent-discovery-v1`, `--approved-bundle-sha256` and `--confirm-live-calls`. Those flags record external approval; they do not grant it. The CLI reconstructs all requests and caps before loading provider credentials, pins the OpenAI destination, and uses zero SDK retries. The approved run supplied these flags once; its original claim and result are retained. Do not reuse them to replay the attempt.

A permanent `.m7-recent-discovery-v1.claimed` file and fsynced reservation ledger live beside the frozen bundle. `discovery-results-v1.json` contains query/request hashes, safe outcomes/usage, ordered consulted-source references and access-review-required markers. Do not delete/copy artifacts to replay a spent approval; any crash or failed attempt requires inspection and a new explicit decision. Full responses, model narrative and unknown/capability fields are discarded. Only the new local evaluation artifacts are written; the app database, evidence corpus and old execution records are not opened for mutation.

## After discovery

1. Inspect the actual candidate URLs, provider-reported publishers and titles offline. A hostname is not proof of the publisher's identity or permission. Record duplicates, misses and uncertain relevance without forcing matches.
2. Prepare a concrete source-retrieval list and separate HTTP budget. Review actual publisher identity, aliases, terms and robots rules before acquiring content; preserve the access-response bytes/hashes and reasons so access decisions can be replayed. Earlier rejected publishers and authentication/paywall/challenge boundaries remain excluded. Provider search access does not authorize DealSage retrieval, retention or republishing. This discovery stage makes **zero direct page/robots/registry requests** and does not solve the existing page-sanitation or publisher-alias gap.
3. Only after permitted retrieval, retain attributed event/announcement dates and exact supporting excerpts. Recent cited claims can qualify under the shared intake policy; older and unverifiable claims remain background or verification work. Add business activity/size/fit clues with source attribution and no invented financials or ownership.
4. Freeze up to three eligible packets through preparation v3/execution v4, obtain separate exact-packet model-transfer/budget approval, and measure usefulness of the resulting business briefs through actual human review. The current 0/3 outcome stays preserved. Zero eligible packets means no analysis spend.

This protocol prepares discovery, not Milestone 7 completion or live precision validation. Issue #92 remains deferred.

## Observed execution outcome

Issue #130 approved recent discovery stopped after its first query. The provider returned 9,058 input and 932 output tokens, but a subsequent ValueError failed response validation; the historical record lacks the per-check detail needed to identify the cause. Zero candidates or source evidence were retained and seven slots were unattempted. The reservation is $0.12; the recorded estimate is $0.0141285 using the planned one-search fee, not an invoice or proof of actual tool count. The result SHA-256 is `60a423857868c2f3a34f1ee85e4c1564da3b11251a24e31488452d3bfc0a11b7`. The one-shot claim and original result remain immutable, and this run approval is exhausted. Future attempts now have safe versioned per-check diagnostics and bounded response-status/model-match/tool-count observations; this cannot reconstruct the discarded response. All 25 discovery guard tests passed before execution and again after the diagnostic change. No retry, direct source/registry retrieval, corpus write, separate analysis or promotion ran. Milestone 7 and #130 remain open, and human usefulness remains 0/3. A new attempt requires a separately versioned, reviewed execution decision; never delete the claim to replay.

The saved usage proves that the response reached the usage check. It does not distinguish model mismatch, incomplete status, unexpected tool count, invalid source structure, oversized reference or sanitation failure. No response body was retained, so none of those causes is asserted retrospectively. Future diagnostic codes identify the failed check without logging provider/source text. The request contract, budgets and replay refusal are unchanged.
