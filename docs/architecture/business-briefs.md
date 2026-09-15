# Business research briefs

Issue #145 adds the read-only `business-brief-v1` projection to `/api/research/case-narratives`. It reuses case evidence, asserted claims, the shared signal-intake result, contradictions and pending frontier questions. Reading a brief does not write evidence, assessments, model proposals or analyst conclusions, reserve cost, or promote a candidate. There is no schema migration or new enrichment provider.

## Attribution and unknowns

Only explicit retained `extracted_facts` keys are projected: business_name/legal_name/business_clue, location/city/state, industry/business_activity, employee_count, revenue/ebitda and company_type. Asserted claim business/business_name labels are also retained. Every fact carries evidence ID, publisher, canonical URL and its original source-fact or third-party-estimate classification. Values are displayed literally; financial currency, units and time periods are not inferred. Missing values remain unknown. Collectors that do not populate these keys will not acquire richer facts merely by rendering the brief.

A single distinct reported business name supplies the headline. Multiple names are shown as unresolved alternatives; no name is resolved from a hypothesis, model summary or person role. Exact source-reported public-company labels indicate a mismatch with the current private-company acquisition focus; competing names or public/private assertions require reconciliation. This is a reported target-fit clue, not a comprehensive entity classification or attractiveness score.

## Timing and ordering

The existing opt-in `signal-intake-v1` assessment policy supplies eligibility, dates and frozen lookback. Without a policy, the brief cannot claim current eligibility. The selected asserted transition prefers an eligible claim, then claim ID for reproducibility. Eligible cases sort first, date-review cases next, historical background last; explicitly reported public-company mismatches also sort last. Sorting is a presentation heuristic, not ownership confidence or opportunity scoring. Within each group the existing case order is preserved. Planned events, recent announcements, reported/completed events and historical background have distinct visible status. Open contradictions remain visible and can prevent timing eligibility through the shared intake policy.

Deterministic signal-type language explains potential business relevance. Historical language explicitly describes background. The next gap uses retained pending frontier work where appropriate, or a business/signal-specific date, conflict or relationship question. It never implies sale intent or ownership from a role.

## Research surface

Business briefs appear before the collapsed source-operations/historical-experiment section, even if those unrelated requests fail. Supporting transition excerpts expand inline; individual facts retain clickable citations. URLs must be HTTP(S) without embedded credentials, and React renders research text without HTML interpretation. Detailed transition evidence, original model proposals/dispositions, confidence factors and analyst conclusions remain accessible in secondary case details.

The latest completed, non-rejected proposal with a summary may appear as separately labeled original model insight, including proposal/evidence IDs and review disposition. Corrections remain in the review record; model text never supplies source facts or silently replaces analyst decisions. Existing scoring and promotion guards are unchanged.

## Validation boundary

The tracked fictional JSON fixture is generated from actual in-memory API output using `tests/test_lead_briefs.py:fictional_cases`; it is not a research-corpus export. Tests and rendered desktop/narrow inspection cover recent ownership-uncertain research, historical completion, a public-company mismatch, a future plan, and unresolved contradiction. The UI remains readable with unavailable historical queries. No live source/model calls or real database writes were performed.

Milestone 7 closeout rendered the actual business-brief projection for recent Utah/Colorado packets and the additional Texas planned-ownership packet. Source assertions, original model text and human judgments remain separate. New usefulness is unmeasured; the original 0/3 useful result remains unchanged. The completed evaluation does not establish calibrated recommendation quality. See [the outcome](../research/milestone7-closeout.md).

## Reviewer inbox (Issue #156)

The authenticated `/api/research/inbox` returns case narratives with total/page/page_size (1–50 per page), ordered by case update time and ID for stable ties. `/api/research/cases/{id}` addresses any retained case without a candidate or resolved entity. Existing `/case-narratives` remains compatible. The inbox is the landing route; source operations and historical candidate views keep their routes.

State matches linked entity geography or an explicit retained state assertion; it is not an identity judgment. Signal/date filters must match the same asserted transition claim. Event dates use existing calendar validation; the alternative publication-date basis never substitutes retrieval time. These are assertion filters, not current signal eligibility, source corroboration or modified frozen policy. A case can match one claim and still show contradictory assertions. Unfiltered views retain undated cases. Current SQL/JSON storage requires streaming transition metadata for these filters; only the selected page receives full narratives. Large-corpus filter indexing remains unbenchmarked.

Linked business and candidate IDs are exposed separately from source-reported business names. Model dispositions, analyst conclusions and research state remain distinct. Reading the inbox does not reserve spend, modify a case or promote a candidate. No new schema or scoring version is introduced. Candidate detail now renders existing score provenance and source-specific demo/classification labels; absent reviews and unavailable resources have explicit UI states. Pilot sign-out clears the server session and browser query cache.

## Saved case versions (Issue #170)

The case page now supports explicit immutable [brief versions](brief-versions.md). Source-backed projection, original cited model observations and human judgments remain separate; a later source addition cannot rewrite an earlier version. This does not change the live inbox projection or scoring.
