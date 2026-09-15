# Milestone 8: intelligence before reviewer handoff

Status: required M8 remediation under [Issue #194](https://github.com/davejensen34/deal-sage/issues/194), following user feedback on September 15, 2026. This is an implementation plan, not a delivered capability. [Issue #187](https://github.com/davejensen34/deal-sage/issues/187) acceptance is paused. Existing engineering increments and the original acquisition history remain intact.

## Product correction

The reviewer should receive a business opportunity with a supported reason to spend attention on it. DealSage must discover leads, investigate the important unknowns, reconcile evidence and evaluate fit before that handoff. The reviewer then decides whether and how to pursue the opportunity. Asking the reviewer to assemble the intelligence from search links, run each query and judge raw capture transfers the product's core work to the user.

Usefulness ratings are a product-evaluation instrument, not the normal transaction or a prerequisite to value. The user has rejected the readiness of the current packets; no individual usefulness ratings or review times are inferred. Preserve all ten packets and failures as a diagnostic baseline. Do not ask the user to complete the prior exercise until the machine-side intelligence work is ready.

"Recommended for review" means DealSage has evidence-backed reasons that a business matches the saved target profile and that a transition matters for the stated purpose. It does not mean every source is true, ownership is proven, or a business is for sale. Confidence, contradictions and gaps belong alongside the recommendation. A completed run can legitimately find no qualifying opportunities; that is an honest outcome, not a successful recommendation transaction.

## What inspection found

| Implementation | Present behavior | Missing outcome |
| --- | --- | --- |
| `apps/api/app/research/discovery_runs.py` | Frozen state/signal queries, reservations and durable source-link staging | A run that continues through investigation to recommendations |
| `apps/api/app/research/followups.py` | Reviewer supplies question, rationale and exact query; search plan has zero retrieval/analysis calls | System selects and executes useful next research within the authorized scope |
| `apps/api/app/research/extraction_attempts.py` | One excerpt; exact quotation and schema validation | Semantic field validation and combined evidence assessment; citation equality did not prevent partner counts being called employee counts |
| `apps/api/app/research/lead_briefs.py` | Retained fact fields, generic signal relevance, limited public-company fit handling | Purpose-specific target fit and a supported explanation of why this business is worth attention now |
| `apps/api/app/research/brief_versions.py` | Immutable source/model/human snapshots | A snapshot of a completed assessment, rather than a substitute for producing one |
| `model_analysis.py`, `identity_resolution.py`, `frontier.py`, `loop.py` | Existing analysis, identity and bounded execution components | Integrated durable orchestration in the M8 user journey; legacy approved-step contracts cannot simply be bypassed |

`test_lead_briefs.py` protects unknowns, provenance and presentation; it does not prove discovery-to-recommendation quality. The live cohort was manually assembled by the coding agent, came from one publisher, and left useful facts outside the main brief. Passing infrastructure tests and receiving complete model responses did not establish the intended product outcome.

The current live discovery path connects OpenAI web search. An Anthropic structured-analysis adapter exists, but that is not Claude web-search integration. Additional search APIs are not implemented by naming them in a plan. Each provider must expose supported capabilities, citation/source provenance, usage, limits and safe failure behavior; validate actual adapters before claiming coverage. Multiple providers repeating the same source are not independent corroboration.

## Required transaction

1. **Define the target.** Save and freeze purpose, geography, transition families/recency, industry, company type, size preferences and exclusions. Distinguish required factors from preferences and unknown from mismatch. Do not invent numerical revenue/employee targets. Existing private-company acquisition focus remains the default for acquisition; a marketing-purpose evaluation must not silently become the universal product profile.
2. **Authorize one bounded investigation.** Freeze run-wide query, retrieval, model, elapsed-time and monetary limits. Execute ordinary permitted steps within that allowance without repeated approvals. Show progress and allow cancellation. Restriction, exhausted budget, changed destination/scope or uncertain access is an explicit exception. This is a user-started investigation, not a recurring unattended crawler.
3. **Discover and capture.** Support signal-first, business-first and hybrid starts. Extract candidate businesses from useful source pages and linked announcements with retained derivation order and lineage. Retrieve bounded relevant document sections with source hashes and dates; do not rely only on the first 2,000 characters or silently discard later business context. Keep search snippets as clues until grounded in inspectable evidence.
4. **Investigate and reconcile.** Select next questions by material uncertainty and expected value: resolve business/person identity, confirm what changed and when, assess current operations, establish geography/profile fit and seek independent supporting or conflicting evidence. Use permitted business websites, public business profiles, evaluated registries and relevant reporting. Registry roles are not ownership proof. Preserve alternate hypotheses, duplicates/syndication, event versus announcement dates and planned versus completed transitions.
5. **Assess and explain.** Produce a versioned DealSage assessment with citations, fit factors, transition relevance, business activity/size clues, support/conflicts, material gaps and a concrete appropriate next step. Models assist extraction, question selection and synthesis. Deterministic rules validate inputs, control execution, calculate authoritative fit/readiness and record routing. Model observations are not silently copied into source facts or human conclusions.
6. **Hand off useful work.** Lead the inbox with recommendations that satisfy the frozen readiness contract. Keep further-research, insufficient-evidence, not-fit and budget-stopped records available in research history. Human review governs pursuit, judgment and communication; it does not need to approve every ordinary extraction or assign a usefulness label before seeing an assessment.

## Readiness and execution contracts to implement

Before the first implementation PR, freeze versioned required/preferred factors and inspectable reasons for each routing outcome. Recommended-for-review requires a sufficiently supported business identity (more than name alone), a source-supported relevant transition/announcement and timing, required target factors met, and a purpose-specific rationale supported by cited observations. Material identity/transition contradictions block recommendation until resolved or explicitly represented in a qualified assessment. Missing hard-required fit evidence routes to further research or insufficient evidence; missing optional financials stays unknown. Do not require ownership proof for every marketing opportunity, or infer sale intent for acquisition opportunities.

Use SQL-persisted run stages and existing reservation/idempotency patterns. A parent allowance must account for all child searches/retrievals/model work, including failures, interrupted outcomes and retries. Do not sum overlapping ledgers twice or mutate old frozen budgets. Persist checkpoints and make resume/cancellation behavior explicit before introducing a worker; no new distributed infrastructure is justified. Deduplicate repeated questions/URLs and stop on sufficient support, repeated no gain, access restrictions, time or budget. Source access policy is separate from truth assessment; uncertainty triggers more research where worthwhile, not automatic rejection of the clue.

Use immutable assessment versions linked to the original case/evidence/proposals. Preserve source evidence, DealSage inference and human decisions as distinct records, consistent with ADR-003 and ADR-008. Existing CandidateMatch promotion and human decision contracts remain intact. Do not call an assessment a human approval or overwrite the original ten acceptance briefs.

## Delivery order and acceptance reset

Issue #194 is the remediation umbrella; split implementation-ready work into short-lived issue branches and validated PRs in this order:

1. Target-profile/readiness contract and typed assessment data, with negative cases and explicit unknown handling.
2. Durable discovery/capture/corroboration orchestration, semantic extraction regressions and provider capability checks.
3. Cited synthesis, deterministic readiness routing and recommendation-first presentation, with raw history accessible.
4. End-to-end evaluation from an empty run through recommendation/no-match, followed by renewed human acceptance under #187.

Tests must cover same-name mismatches, executive versus owner, branch/tenure versus employee count, publication versus event date, future transitions, person versus business names, stock ticker versus website, syndicated reports, conflicting facts, missing required profile data, restricted sources, provider failure, interruption, duplicate requests and budget exhaustion. Use retained failures for regression without reconstructing the research history through live calls.

Freeze a revised evaluation protocol before live execution: target profile, selection/order, recommendation eligibility, negative controls, cost/operation ceilings and success criteria. Preserve discovery-to-qualified-lead funnel counts and all misses; report cost per run/recommendation and provenance coverage. Do not replace unhelpful records until the denominator appears successful. Actual human acceptance remains necessary for the finished result, but the old ten-record QA request is suspended. A no-result run must remain honest; investigate failure causes rather than invent matches or make the reviewer perform the missing work.

The previous $0.98 reservation record remains unchanged. This planning change makes no live calls, changes no model, expands no spending envelope and does not establish provider prices or quality. Cost controls should support a useful bounded investigation; they are not a reason to hand off unfinished research as a recommendation.

## Next milestone: conversational investigation

[Issue #195](https://github.com/davejensen34/deal-sage/issues/195) captures the user's requested next milestone for planning after M8 remediation. It is not active implementation.

Design a comfortable case-aware and cross-case conversation: ask why a lead fits, inspect a claim, compare businesses, test a hypothesis or ask DealSage to investigate further. Answers should cite saved evidence/assessment versions; new research should use the same bounded orchestration and report what changed, supporting/conflicting sources and remaining budget. Existing-evidence answers and new external research must be distinguishable. Chat must not silently change target profiles, scores, human decisions or send outreach.

Planning deliverables: interaction prototype, conversation/evidence-version contracts, provider capability matrix, authorization/cancellation/recovery flows, and grounded-answer/follow-up acceptance scenarios. Build on the intelligence pipeline, not a second chat-specific research backend. Implementation activation and any new live evaluation remain separate from this recorded planning direction.
